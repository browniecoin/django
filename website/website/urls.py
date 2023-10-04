"""los URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from store import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('home/', views.index, name='index'),
    path('home/success/', views.success_view, name='success'),
    path('home/admin/', admin.site.urls),
    path('home/login/', views.login_view, name='login'),
    path('home/logout/', views.logout_view, name='logout'),
    path('home/add_user/', views.add_user, name='add_user'),
    path('home/edit_profile/', views.edit_profile, name='edit_profile'),
    # Add additional URLs for success and failure views
    path('home/success/', views.success, name='success'),
    path('home/failure/', views.failure, name='failure'),
    path('home/accounts/', include('allauth.urls')),
    path('home/social-auth/', include('social_django.urls', namespace='social')),
    path('home/my_profile/', views.my_profile, name='my_profile'),
    path('home/my_profile_accounts/', views.my_profile_accounts, name='my_profile_accounts'),
    path('home/my_profile_accounts_add/', views.my_profile_accounts_add, name='my_profile_accounts_add'),
    path('home/add_idv/', views.add_idv, name='add_idv'),
    path('home/add_kyc/', views.add_kyc, name='add_kyc'),
    path('home/add_bank_account/', views.add_bank_account, name='add_bank_account'),
    path('home/add_spend/', views.add_spend, name='add_spend'),
    path('home/account_detail/', views.account_detail, name='account_detail'),
    path('home/account_detail_first/', views.account_detail_first, name='account_detail_first'),
    path('home/pay_with_stripe/', views.pay_with_stripe, name='pay_with_stripe'),
    path('home/add_card/', views.add_card, name='add_card'),
    path('home/account_detail_update/', views.account_detail_update, name='account_detail_update'),
    path('home/account_detail_statements/', views.account_detail_statements, name='account_detail_statements'),
    path('home/account_detail_statement/', views.account_detail_statement, name='account_detail_statement'),
    path('home/get_csrf_token/', views.get_csrf_token, name='get_csrf_token'),
    path('home/add_phone/', views.add_phone, name='add_phone'),
    path('home/verify_email/', views.verify_email, name='verify_email'),
    path('home/add_ssn_dob/', views.add_ssn_dob, name='add_ssn_dob'),
    path('home/add_first_bank_account_and_cc/', views.add_first_bank_account_and_cc, name='add_first_bank_account_and_cc'),
    path('home/add_card_first/', views.add_card_first, name='add_card_first'),
    path('home/get_card/', views.get_card, name='get_card'),
    path('home/pull_funds/', views.pull_funds, name='pull_funds'),
    path('home/get_contacts/', views.get_contacts, name='get_contacts'),
    path('home/add_contact/', views.add_contact, name='add_contact'),
    path('home/edit_contact/', views.edit_contact, name='edit_contact'),
    path('home/contact_detail/', views.contact_detail, name='contact_detail'),
    path('home/make_payment/', views.make_payment, name='make_payment'),
    path('home/send_intrabank/', views.send_intrabank, name='send_intrabank'),
    path('home/delete_contact/', views.delete_contact, name='delete_contact'),
    path('home/send_ach/', views.send_ach, name='send_ach'),
    path('home/send_domestic_wire/', views.send_domestic_wire, name='send_domestic_wire'),
    path('home/send_check/', views.send_check, name='send_check'),
    path('home/add_wallet/', views.add_wallet, name='add_wallet'),
    path('home/get_wallet_history/', views.get_wallet_history, name='get_wallet_history'),
    path('home/get_leaders/', views.get_leaders, name='get_leaders'),


]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
