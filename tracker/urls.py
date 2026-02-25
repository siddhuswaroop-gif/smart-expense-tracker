from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_transaction, name='add_transaction'),
    path('transactions/', views.transactions_list, name='transactions_list'),
    path('edit/<int:id>/', views.edit_transaction, name='edit_transaction'),
    path('delete/<int:id>/', views.delete_transaction, name='delete_transaction'),

    path('breakdown/', views.category_breakdown, name='category_breakdown'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
]