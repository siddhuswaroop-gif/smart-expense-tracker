from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from datetime import datetime
from .models import Transaction, Category, Budget
from .forms import TransactionForm
import json

def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "tracker/login.html")


def signup_view(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, "Account created successfully")
            return redirect('login')

    return render(request, "tracker/signup.html")


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):

    transactions = Transaction.objects.filter(user=request.user)

    selected_month = request.GET.get('month')

    if selected_month and selected_month.isdigit():
        selected_month_int = int(selected_month)
        transactions = transactions.filter(date__month=selected_month_int)
    else:
        selected_month_int = None

    income = transactions.filter(type='INCOME').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = transactions.filter(type='EXPENSE').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = income - expenses

    total_transactions = transactions.count()

    highest_expense = transactions.filter(type='EXPENSE').order_by('-amount').first()
    highest_income = transactions.filter(type='INCOME').order_by('-amount').first()

    recent_transaction = transactions.order_by('-created_at').first()


    current_month = selected_month_int if selected_month_int else datetime.now().month
    current_year = datetime.now().year

    budget_obj = Budget.objects.filter(
        user=request.user,
        month=current_month,
        year=current_year
    ).first()

    budget_amount = float(budget_obj.amount) if budget_obj else 0

    spent = float(
        transactions.filter(type='EXPENSE')
        .aggregate(Sum('amount'))['amount__sum'] or 0
    )

    remaining = budget_amount - spent if budget_amount else 0

    percentage = 0
    if budget_amount > 0:
        percentage = int((spent / budget_amount) * 100)
        if percentage > 100:
            percentage = 100


    monthly_data = (
        Transaction.objects
        .filter(user=request.user)
        .values('date__month')
        .annotate(
            income=Sum('amount', filter=Q(type='INCOME')),
            expenses=Sum('amount', filter=Q(type='EXPENSE'))
        )
        .order_by('date__month')
    )

    months = []
    income_data = []
    expense_data = []

    for row in monthly_data:
        months.append(f"Month {row['date__month']}")
        income_data.append(float(row['income'] or 0))
        expense_data.append(float(row['expenses'] or 0))


    category_data = (
        Transaction.objects
        .filter(user=request.user, type='EXPENSE')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    pie_labels = [row['category__name'] for row in category_data]
    pie_totals = [float(row['total']) for row in category_data]

    return render(request, 'tracker/dashboard.html', {
        'income': income,
        'expenses': expenses,
        'balance': balance,
        'selected_month': selected_month,
        'total_transactions': total_transactions,
        'highest_expense': highest_expense,
        'highest_income': highest_income,
        'recent_transaction': recent_transaction,

        'budget': budget_amount,
        'spent': spent,
        'remaining': remaining,
        'percentage': percentage,

        'months': json.dumps(months),
        'income_data': json.dumps(income_data),
        'expense_data': json.dumps(expense_data),

        'pie_labels': json.dumps(pie_labels),
        'pie_totals': json.dumps(pie_totals),
    })


@login_required
def add_transaction(request):

    if request.method == 'POST':
        form = TransactionForm(request.POST)

        if form.is_valid():
            txn = form.save(commit=False)
            txn.user = request.user
            txn.save()
            return redirect('dashboard')

    else:
        form = TransactionForm()

    return render(request, 'tracker/add_transaction.html', {'form': form})


@login_required
def transactions_list(request):

    transactions = Transaction.objects.filter(user=request.user)

    txn_type = request.GET.get('type')
    category = request.GET.get('category')
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    if txn_type and txn_type != "ALL":
        transactions = transactions.filter(type=txn_type)

    if category and category != "ALL":
        transactions = transactions.filter(category_id=category)

    if start_date:
        transactions = transactions.filter(date__gte=start_date)

    if end_date:
        transactions = transactions.filter(date__lte=end_date)

    categories = Category.objects.all()

    return render(request, 'tracker/transactions_list.html', {
        'transactions': transactions.order_by('-date'),
        'categories': categories,
        'selected_type': txn_type,
        'selected_category': category,
        'start_date': start_date,
        'end_date': end_date,
    })


@login_required
def edit_transaction(request, id):

    txn = get_object_or_404(Transaction, id=id, user=request.user)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=txn)

        if form.is_valid():
            form.save()
            return redirect('transactions_list')

    else:
        form = TransactionForm(instance=txn)

    return render(request, 'tracker/add_transaction.html', {'form': form})



@login_required
def delete_transaction(request, id):

    txn = get_object_or_404(Transaction, id=id, user=request.user)
    txn.delete()

    return redirect('transactions_list')



@login_required
def category_breakdown(request):

    transactions = Transaction.objects.filter(
        user=request.user,
        type='EXPENSE'
    )

    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    if start_date:
        transactions = transactions.filter(date__gte=start_date)

    if end_date:
        transactions = transactions.filter(date__lte=end_date)

    data = (
        transactions
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    labels = [row['category__name'] for row in data]
    totals = [float(row['total']) for row in data]

    return render(request, 'tracker/category_breakdown.html', {
        'data': data,
        'labels': json.dumps(labels),
        'totals': json.dumps(totals),
        'start_date': start_date,
        'end_date': end_date,
    })