from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('produto/<str:produto_id>/', views.produto_detalhes, name='produto_detalhe'),
    # path('produto/<int:produto_id>/', views.produto_detalhes, name='produto_detalhe'),
    path('categoria/<str:categoria_id>/', views.produtos_por_categoria, name='produtos_por_categoria'),
    path('search/', views.search, name='search'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('compra_sucesso/', views.success, name='compra_sucesso'),
    path('finalizar_compra/', views.finalizar_compra, name='finalizar_compra'),
    path('register/', views.register, name='register'),
    path('criar-checkout-session/', views.criar_checkout_session, name='criar_checkout_session'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    path('ver_carrinho/', views.ver_carrinho, name='ver_carrinho'),
    path('remover_do_carrinho/<str:produto_id>/', views.remover_do_carrinho, name='remover_do_carrinho'),
    path('adicionar_ao_carrinho/<str:produto_id>/', views.adicionar_ao_carrinho, name='adicionar_ao_carrinho'),
]

