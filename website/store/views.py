import datetime
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse

from django.http import FileResponse, Http404
from django.http import JsonResponse
from django.http import HttpResponse

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test

from django.views.generic.edit import CreateView
from django.views.generic import View


from django.core.paginator import Paginator
from django import template

from django.middleware.csrf import get_token  # Import get_token

import requests
import os
import csv
import io
import random
from io import BytesIO
import socket
import uuid

import urllib.request
from django.core.files.base import ContentFile

from django.db.models import Q

import json

from .models import User, UserManager, BankAccount, PhoneVerification, TokenRecord, TokenBalance, CoinStats, MagicKey
from .forms import UserCreationForm, EditProfileForm

import stripe
from PIL import Image
import openai
from twilio.rest import Client

import pytz


from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


from eth_account import Account
from web3 import Web3
from eth_account.messages import encode_defunct
import time
import eth_keys.exceptions
from collections import defaultdict

from django.core import serializers
import requests
import qrcode
from PIL import Image
from io import BytesIO

register = template.Library()

def verify_signed_message(message, signature, public_address):
    # Skip signature verification if signature, account address, or message is empty
    if not signature or not public_address or not message:
        return False

    message = encode_defunct(text=message)

    # Verify the signature
    try:
        signer = Account.recover_message(message, signature=signature)
    except:
        # Signature verification failed
        return False

    # Verify if the signer's address matches the provided public address
    return signer == public_address

def get_csrf_token(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrf_token': csrf_token})

def generate_id():
    return uuid.uuid4().hex




def index(request):
    cart_id = request.COOKIES.get('cartId')
    if cart_id is None:
        cart_id = generate_id()

    search_key = request.GET.get('search_key', '')
    if request.method == 'POST':
        search_key = request.POST.get('search_key', '')

    context = {'cart_id': cart_id, 'request': request, 'search_key': search_key}
    response = render(request, 'index.html', context)
    response.set_cookie('cartId', cart_id)
    return response

    return render(request, 'index.html', context)


def coin_stats(request):
    # Get the last 200 CoinStats objects
    coin_stats_data = CoinStats.objects.order_by('-timestamp')[:50]

    # Serialize the data to JSON
    data = serializers.serialize('json', coin_stats_data)

    # Return the JSON response
    return JsonResponse(data, safe=False)


def success_view(request):
    return render(request, 'success.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('my_profile')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        # Handle form submission
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('edit_profile')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'edit_profile.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('/login')

def add_user(request):
    print("add user invoked")

    phone = request.POST.get('phone', None)
    code = request.POST.get('code', None)
    action = request.POST.get('action', None)

    if request.method == 'POST' and action == 'save':
        print("add user invoked 2")
        content_type = request.META.get('CONTENT_TYPE', '').lower()

        if content_type == 'application/json':
            try:
                # Parse JSON data from the request body
                json_data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)

            field_mapping = {
                'username': 'username',
                'email': 'email',
                'first_name': 'first_name',
                'last_name': 'last_name',
                'm_name': 'm_name',
                'password': 'password',
            }

            form_data = {}
            for json_key, form_field in field_mapping.items():
                if json_key in json_data:
                    form_data[form_field] = json_data[json_key]

            form = UserCreationForm(form_data)
        else:
            form = UserCreationForm(request.POST)

        try:
            existing_record = PhoneVerification.objects.filter(phone_number=phone, verification_code=code).first()
            if existing_record:
                if form.is_valid():
                    user = form.save(commit=False)
                    user.set_password(form.cleaned_data['password'])
                    user.phone = phone
                    user.save()
                    print("USER SAVED")
                    # Authenticate the user after registration
                    user = authenticate(username=user.username, password=form.cleaned_data['password'])
                    if user is not None:
                        login(request, user)  # This logs the user in
                        if content_type == 'application/json':
                            return JsonResponse({'message': 'User created and logged in successfully'}, status=201)
                        else:
                            return redirect('my_profile')
                    else:
                        # Handle authentication failure
                        if content_type == 'application/json':
                            return JsonResponse({'message': 'User registration successful, but login failed'}, status=201)
                        else:
                            return redirect('login')
                else:
                    return JsonResponse({'errors': form.errors}, status=400)
            else:
                print("NO PHONE AND CODE RECORD FOUND")
                return render(request, 'add_user.html', {'form': form, 'phone': phone, 'code': code})
        except Exception as e:
            # Handle other exceptions here, if necessary
            return JsonResponse({'error': str(e)}, status=500)

    else:
        '''
        # iOS json sign service will remove later
        print("add user invoked 4")
        content_type = request.META.get('CONTENT_TYPE', '').lower()
        if content_type == 'application/json':
            print("add user invoked 78")
            try:
                # Parse JSON data from the request body
                json_data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)

            field_mapping = {
                'username': 'username',
                'email': 'email',
                'first_name': 'first_name',
                'last_name': 'last_name',
                'password': 'password',
            }

            form_data = {}
            for json_key, form_field in field_mapping.items():
                if json_key in json_data:
                    form_data[form_field] = json_data[json_key]

            form = UserCreationForm(form_data)
            if form.is_valid():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                return JsonResponse({'message': 'User created successfully'}, status=201)
            '''
        form = UserCreationForm()

    return render(request, 'add_user.html', {'form': form, 'phone': phone, 'code': code})

def get_leaders(request):
    # Query TokenBalance and order by token_count in descending order
    leaders = TokenBalance.objects.order_by('-token_count')[:5]

    # Create a dictionary (map) to store User objects by wallet_address
    user_map = defaultdict(list)

    # Query User objects and populate the dictionary by wallet_address
    users = User.objects.all()
    for user in users:
        if user.wallet_address:
            user_map[user.wallet_address].append(user)

    # Serialize leaders into a JSON response with associated User information
    serialized_leaders = []
    for leader in leaders:
        leader_info = {
            'token_owner': leader.token_owner,
            'token_count': leader.token_count,
            'balance': float(leader.balance),
        }

        # Check if there is a User associated with the leader's wallet_address
        associated_users = user_map.get(leader.token_owner, [])
        if associated_users:
            # Serialize the User information and add it to the leader's info
            leader_info['associated_users'] = [
                {
                    'username': user.username,
                    'email': user.email,
                    'x_handle': user.x_handle,  # Include the x_handle field
                    # Add other user fields as needed
                }
                for user in associated_users
            ]

        serialized_leaders.append(leader_info)

    # Create a JSON object to wrap the serialized leaders
    response_data = {
        'leaders': serialized_leaders
    }

    return JsonResponse(response_data)

def get_wallet_history(request):
    wallet_address = request.GET.get('wallet_address', '')
    ## NEW CODE
    # Query 1: Get token records
    token_records = TokenRecord.objects.filter(token_owner=wallet_address)

    # Query 2: Get token balances
    token_balances = TokenBalance.objects.filter(token_owner=wallet_address)

    # You now have the token records and balances for the given wallet_address
    # You can use these results to display or process the wallet history as needed

    # Example usage: printing the results
    for record in token_records:
        print(f"Token Record: {record}")

    for balance in token_balances:
        print(f"Token Balance: {balance}")

    # Create a dictionary to store the combined data
    wallet_history = {
        'token_records': [record.__str__() for record in token_records],
        'token_balances': [balance.__str__() for balance in token_balances],
    }

    # Serialize the dictionary into a JSON response
    response_data = json.dumps(wallet_history)

    # Return a JSON response
    return JsonResponse(response_data, safe=False)

@login_required
def add_wallet(request):
    user = request.user
    content_type = request.META.get('CONTENT_TYPE', '').lower()

    if content_type == 'application/json':
        try:
            # Parse JSON data from the request body
            json_data = json.loads(request.body.decode('utf-8'))
            print(json_data["key"])
            print(json_data["accountAddress"])
            key = json_data["key"]
            message = json_data["value"]
            signer_address = json_data["accountAddress"]
            signature = json_data["signature"]

            is_valid = verify_signed_message(key, signature, signer_address)


            # Compare the recovered address with the provided address
            if is_valid :
                user.wallet_address = signer_address
                user.save()
                print("Signature is valid!")
            else:
                user.wallet_address = "0x00"
                user.save()
                print("Signature is invalid.")

            print(json_data)
        except Exception as e:
            print(f"JSON Decode Error: {e}")
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    return redirect('my_profile')

@login_required
def verify_email(request):
    user = request.user
    code = request.POST.get('code', '')

    if code == '':
        print("CODE IS EMPTY")
        code = generate_random_six_digit_code()
        print(code)
        current_utc_time = datetime.datetime.now(pytz.utc)
        user.email_verification_code = code
        user.email_timestamp = current_utc_time
        user.email_verification_tries = 0
        user.save()

        senderemail  = "info@motoverse.app"
        messagebody  = "Email verifiaction code " + code
        messagesub = "Email Verifiaction Code"
        messageto = user.email

        message = Mail(
            from_email=senderemail,
            to_emails=messageto,
            subject=messagesub,
            html_content=messagebody)
        #sg = SendGridAPIClient(os.environ.get('SENDGRID_AUTH'))
        #sg = SendGridAPIClient('')
        #response = sg.send(message)
        #print(response.status_code, response.body, response.headers)

        # UNCOMMENT FOR PRODUCTION
        # code = ''
        return render(request, 'add_email_code.html' , {'code': code})
    else :
        if user.email_verification_code == code :
            user.email_isVerified = True
            user.save()
            return redirect('my_profile')
        else :
            user.email_verification_tries += 1
            user.save()

    return render(request, 'add_email_code.html')

def success(request):
    return render(request, 'success.html')

def failure(request):
    return render(request, 'failure.html')


def generate_random_six_digit_code():
    # Generate a random six-digit numeric code
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def add_phone(request):
    if request.method == 'POST':
        print("POST request detected")
        print("Profile form saved")
        # Extract form field values
        phone = request.POST.get('phone')
        code = request.POST.get('code', '')

        if code == '':
            print("CODE IS EMPTY")
            # The 'code' field is empty, so you can handle it accordingly
            # For example, you can return an error message or perform some other logic
            try:
                ## Generate a a six digit verification code
                code = generate_random_six_digit_code()
                print(code)
                current_utc_time = datetime.datetime.now(pytz.utc)
                phone_verification = PhoneVerification(phone_number=phone, verification_code=code, timestamp=current_utc_time)
                phone_verification.save()
                twilio_number = os.environ.get('TWILIO_PHONE')
                account_sid = os.environ.get('TWILIO_SID')
                auth_token = os.environ.get('TWILIO_AT')
                client = Client(account_sid, auth_token)
                messageto = phone
                messagebody = "Verification code is: " + code
                message = client.messages.create(
                    to=messageto,
                    from_=twilio_number,
                    body=eval(f"f'{messagebody}'")
                )

                print(f"SMS sent {messageto} with message ID: {message.sid}")

                return render(request, 'add_phone_code.html' , {'phone': phone, 'code': code})
            except Exception as e:
                # Handle any exceptions that may occur during the save operation
                # You can log the error or return an error message to the user
                print(e)
                return render(request, 'add_phone_code.html', {'phone': phone, 'error_message': str(e)})
        else:

            try:
                existing_record = PhoneVerification.objects.filter(phone_number=phone).first()
                if existing_record:
                    print("RECORD FOUND")
                    if existing_record.verification_tries > 5 :
                        print(str(existing_record.verification_tries))
                        return render(request, 'add_phone_code.html', {'phone': phone, 'error_message': 'Over 5 attempts'})
                else:
                    print("NO RECORD FOUND")
                # Check if a record with the provided phone and code exists in the database
                existing_record = PhoneVerification.objects.filter(phone_number=phone, verification_code=code).first()
                if existing_record:
                    # A record with the same phone and code combination already exists
                    print("Record with the same phone and code exists:")
                    print(f"Phone: {existing_record.phone_number}, Code: {existing_record.verification_code}")
                    existing_record.isVerified = True
                    existing_record.save()
                    print("SAVED")
                    return render(request, 'add_phone_success.html', {'phone': phone, 'code': code})
                else:
                    # No matching record found, you can handle it as needed
                    # ADD LOGIC
                    existing_record = PhoneVerification.objects.filter(phone_number=phone).first()
                    existing_record.verification_tries += 1
                    existing_record.save()
                    print("No matching record found for the given phone and code.")
                    return render(request, 'add_phone_code.html', {'phone': phone, 'error_message': 'No matching record found.'})
            except Exception as e:
                # Handle any exceptions that may occur during the search or rendering
                print(e)
                return render(request, 'add_phone_code.html', {'phone': phone, 'error_message': str(e)})

    return render(request, 'add_phone.html')


@login_required
def add_ssn_dob(request):
    user = request.user
    if request.method == 'POST':
        dateOfBirth = request.POST.get('dateOfBirth')
        idNumber = request.POST.get('idNumber')
        context = {
            'user': user,
            'idNumber': idNumber,
            'dateOfBirth': dateOfBirth
        }
        return render(request, 'add_address.html', context)
    context = {
        'user': user
    }
    return render(request, 'add_ssn_dob.html', context)

@login_required
def pull_funds(request):

    user = request.user
    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1/account"

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": user.solidfi
    }
    account_data = None
    account_id = user.active_bank_acc_id
    base_url = "https://test-api.solidfi.com/v1"
    endpoint = f"{base_url}/account/{account_id}"

    # Make the GET request
    response = requests.get(endpoint, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        account_data = response.json()  # The entire response is the account object

        # Display the desired data
        print("Account ID:", account_data["id"])
        print("Label:", account_data["label"])
        print("Routing Number:", account_data["routingNumber"])
        print("Account Number:", account_data["accountNumber"])
        print("Status:", account_data["status"])
        print("Type:", account_data["type"])
        print("Available Balance:", account_data["availableBalance"])
        print("Currency:", account_data["currency"])
        print("Created At:", account_data["createdAt"])
        print("Modified At:", account_data["modifiedAt"])
        print("Sponsor Bank Name:", account_data["sponsorBankName"])
        # ... Display other desired fields

    else:
        print("Error:", response.status_code)
        print("Response:", response.text)

    context = {
        'user': user,
        'account_data': account_data

    }

    return render(request, 'pull_funds.html', context)

@login_required
def my_profile_accounts_add(request):

    user = request.user
    context = {
        'user': user
    }

    return render(request, 'my_profile_accounts_add.html', context)

@login_required
def my_profile_accounts(request):
    print("Entering my_profile function")

    user = request.user

    if user.email_isVerified == False:
        return redirect('verify_email')

    id_number = request.POST.get('idNumber', '')
    if user.solidfi == None or user.solidfi == '' and id_number == '':
        return redirect('add_ssn_dob')

    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1/account"

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": user.solidfi
    }
    params = {
        "offset": 0,
        "limit": 25,
        "status": "active",
        "type": "personalChecking",
        # Add other filters as needed
    }

    # Make the GET request to the API
    response = requests.get(base_url, params=params, headers=headers)

    total_balance = 0.0
    total_accounts = 0
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json()

        # Extract and print relevant account information
        total_accounts = data["total"]
        print(f"Total accounts: {total_accounts}")
        accounts = data["data"]
        for account in accounts:
            account_id = account["id"]
            account_label = account["label"]
            account_type = account["type"]
            account_status = account["status"]
            account_balance = account["availableBalance"]
            print(f"Account ID: {account_id}")
            print(f"Label: {account_label}")
            print(f"Type: {account_type}")
            print(f"Status: {account_status}")
            print(f"Available Balance: {account_balance}")
            print("------")
            total_balance += float(account_balance)
    else:
            print(f"Request failed with status code: {response.status_code}")

    first_two = accounts[:2]
    remaining = accounts[2:]

    context = {
        'user': user,
        'first_two': first_two,
        'remaining': remaining,
        'total_balance': total_balance,
        'total_accounts': total_accounts
    }

    return render(request, 'my_profile_accounts.html', context)

@login_required
def my_profile(request):
    print("Entering my_profile function")

    user = request.user

    if user.email_isVerified == False:
        print("USER EMAIL NOT VERIFIED")
        return redirect('verify_email')


    if request.method == 'POST':
        print("POST request detected")
        print("Profile form saved")
        # Extract form field values
        x_handle = request.POST.get('x_handle','')
        tg_handle = request.POST.get('tg_handle','')
        ig_handle = request.POST.get('ig_handle','')
        brownie_coin_address = request.POST.get('brownie_coin_address','')



        try:
            user.x_handle = x_handle
            user.tg_handle = tg_handle
            user.ig_handle = ig_handle
            user.brownie_coin_address = brownie_coin_address
            user.save()
        except Exception as e:
            print("Error saving user:", e)
        return redirect('my_profile')
    else:
        print("PRINT GET request detected")

    context = {
        'user': user
    }

    return render(request, 'my_profile_kafka.html', context)


@login_required
def add_kyc(request):
    print("Entering my_profile function")
    user = request.user

    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com"
    person_id = user.solidfi  # Replace with the actual person ID

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }

    api_url = "https://test-api.solidfi.com/v1/person"

    endpoint = f"{person_id}/kyc"

    # Request data to submit a new IDV
    request_data = {
    }

    # Make the API request
    response = requests.post(f"{api_url}/{endpoint}", json=request_data, headers=headers)

    # Check response
    if response.status_code == 200:
        kyc_data = response.json()
        print("KYC submission successful:")
        print("KYC ID:", kyc_data["id"])
        print("Status:", kyc_data["status"])
        print("Results:", kyc_data["results"])
    else:
        print("KYC submission failed with status code:", response.status_code)
        print("Response:", response.text)

    return redirect('add_idv')

@login_required
def add_idv(request):
    print("Entering my_profile function")

    user = request.user


    if not user.idv_info_url :
        api_key = os.environ.get('SOLIDFI')
        base_url = "https://test-api.solidfi.com"
        person_id = user.solidfi  # Replace with the actual person ID

        headers = {
            "Content-Type": "application/json",
            "sd-api-key": api_key,
            "sd-person-id": person_id
        }

        api_url = "https://test-api.solidfi.com/v1/person"

        # Request data to submit a new IDV
        request_data = {
            "action": "new"
        }

        # Make the API request
        response = requests.post(f"{api_url}/{person_id}/idv", json=request_data, headers=headers)

        # Check the response
        if response.status_code == 201:
            idv_info = response.json()
            print("IDV submission successful:")
            print(f"IDV ID: {idv_info['id']}")
            print(f"Verification URL: {idv_info['url']}")
            print(f"Status: {idv_info['status']}")
            status = idv_info['status']

            if status != 'notStarted':
                return redirect('my_profile')

            user.idv_info_url = idv_info['url']
            user.save()
        else:
            print("IDV submission failed.")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")


    if user.solidfi :

        api_key = os.environ.get('SOLIDFI')
        base_url = "https://test-api.solidfi.com"

        headers = {
            "Content-Type": "application/json",
            "sd-api-key": api_key,
            "sd-person-id": user.solidfi
        }

        # Example: Creating a Person
        create_person_url = f"{base_url}/v1/person"
        create_person_response = requests.post(create_person_url, headers=headers)
        create_person_data = create_person_response.json()
        created_person_id = create_person_data.get("personId")

        if created_person_id:
            print("Person created with ID:", created_person_id)
        else:
            print("Failed to create person.")

        # Example: Making a GET request using the created person ID
        get_person_url = f"{base_url}/v1/person"
        get_person_response = requests.get(get_person_url, headers=headers)
        get_person_data = get_person_response.json()

        print("Fetched person data:", get_person_data)

        # Access the 'idv' value
        idv_value = get_person_data['kyc']['results']['idv']

        kyc_address = get_person_data['kyc']['results']['address']
        kyc_dateOfBirth = get_person_data['kyc']['results']['dateOfBirth']
        kyc_fraud = get_person_data['kyc']['results']['fraud']
        kyc_bank = get_person_data['kyc']['results']['bank']

        print("IDV Value:", idv_value)
        print("KYC ADDRESS Value:", kyc_address)
        user.idv_value = idv_value
        user.kyc_address = kyc_address
        user.kyc_dateOfBirth = kyc_dateOfBirth
        user.kyc_fraud = kyc_fraud
        user.kyc_bank = kyc_bank
        user.save()

    kyc_is_approved = (
        user.kyc_address == "approved" and
        user.kyc_dateOfBirth == "approved" and
        user.kyc_fraud == "approved" and
        user.kyc_bank == "approved"
    )
    context = {
        'user': user,
        'kyc_is_approved': kyc_is_approved
    }

    return render(request, 'my_profile_idv.html', context)


@login_required
def account_detail_statement(request):
    print("Entering Satements account function")
    user = request.user
    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1/account"
    person_id = user.solidfi  # Replace with the actual person ID

    account_id = user.active_bank_acc_id
    print(account_id)
    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }
    month = request.GET.get('month')
    year = request.GET.get('year')
    statement = None

    # Define the export format
    export_format = "json"

    # Construct the URL
    url = f"{base_url}/{account_id}/statement/{year}/{month}?export={export_format}"

    # Make the GET request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        statement = response.json()
        # Process the statement data as needed
        print("Statement Data:", statement)
    else:
        print("Error:", response.status_code)


    context = {
        'user': user,
        'statement': statement,
        'month': month,
        'year': year
     }

    return render(request, 'account_detail_statement.html', context)

@login_required
def account_detail_statements(request):
    print("Entering Satements account function")
    user = request.user
    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1/account"
    person_id = user.solidfi  # Replace with the actual person ID

    account_id = user.active_bank_acc_id
    print(account_id)
    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }


    url = f"{base_url}/{account_id}/statement"

    statements = None
    total = None
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()

        total = data["total"]
        statements = data["data"]
        print(total)
        for entry in statements:
            month = entry["month"]
            year = entry["year"]
            created_at = entry["createdAt"]

            print(f"Month: {month}, Year: {year}, Created At: {created_at}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

    context = {
        'user': user,
        'statements': statements,
        'total': total
     }

    return render(request, 'account_detail_statements.html', context)

@login_required
def account_detail_update(request):
    print("Entering update account function")

    user = request.user

    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1/account"
    person_id = user.solidfi  # Replace with the actual person ID

    account_id = user.active_bank_acc_id
    print(account_id)
    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }

    label = request.POST.get('label', 'Primary')

    payload = {
        "label": label
    }

    # Construct the endpoint URL
    endpoint_url = f"{base_url}/{account_id}"

    # Send the PATCH request
    response = requests.patch(endpoint_url, json=payload, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        updated_account_data = response.json()
        print("Account updated successfully:")
        print(updated_account_data)
    else:
        print(f"Failed to update account. Status code: {response.status_code}")
        print(response.text)

    return redirect('account_detail')


@login_required
def edit_contact(request):
    print("Entering my_profile function")

    user = request.user
    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1"
    person_id = user.solidfi  # Replace with the actual person ID

    account_id = request.GET.get('account_id', user.active_bank_acc_id)

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }

    contact = None
    contact_id = request.GET.get('contact_id', None)
    if contact_id == None :
        contact_id = request.POST.get('contact_id', None)


    api_url = f"{base_url}/contact/{contact_id}"
    try:
        response = requests.get(api_url, headers=headers)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            contact = response.json()

            # Print or process the data as needed
            print("Contact ID:", contact.get("id"))
            print("Name:", contact.get("name"))
            print("Email:", contact.get("email"))
            # Add more fields as needed

        else:
            print(f"Request failed with status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")


    if request.method == 'POST':
        account_id = user.active_bank_acc_id
        a_name = request.POST.get('name', '')
        a_email = request.POST.get('email', '')
        a_phone = request.POST.get('phone', '')
        a_interbank_account = request.POST.get('intrabank_account', '')
        a_interbank_account_id = request.POST.get('intrabank_account_id', '')
        ach_accountNumber = request.POST.get('ach_accountNumber', '')
        ach_routingNumber = request.POST.get('ach_routingNumber', '')
        ach_accountType = request.POST.get('ach_accountType', '')
        ach_bankName = request.POST.get('ach_bankName', '')
        wire_accountNumber = request.POST.get('wire_accountNumber', '')
        wire_routingNumber = request.POST.get('wire_routingNumber', '')
        wire_accountType = request.POST.get('wire_accountType', '')
        wire_bankName = request.POST.get('wire_bankName', '')
        wire_addressType = request.POST.get('wire_addressType', '')
        wire_line1 = request.POST.get('wire_line1', '')
        wire_line2 = request.POST.get('wire_line2', '')
        wire_city = request.POST.get('wire_city', '')
        wire_state = request.POST.get('wire_state', '')
        wire_country = request.POST.get('wire_country', '')
        wire_zip = request.POST.get('wire_zip', '')
        check_addressType = request.POST.get('check_addressType', '')
        check_line1 = request.POST.get('check_line1', '')
        check_line2 = request.POST.get('check_line2', '')
        check_city = request.POST.get('check_city', '')
        check_state = request.POST.get('check_state', '')
        check_country = request.POST.get('check_country', '')
        check_zip = request.POST.get('check_zip', '')
        card_addressType = request.POST.get('card_addressType', '')
        card_line1 = request.POST.get('card_line1', '')
        card_line2 = request.POST.get('card_line2', '')
        card_city = request.POST.get('card_city', '')
        card_state = request.POST.get('card_state', '')
        card_country = request.POST.get('card_country', '')
        card_zip = request.POST.get('card_zip', '')
        show_ach_detail = request.POST.get('show_ach_detail', None)
        show_wire_detail = request.POST.get('show_wire_detail', None)
        show_wire_detail_address = request.POST.get('show_wire_detail_address', None)
        show_check_detail = request.POST.get('show_check_detail', None)
        show_card_detail = request.POST.get('show_card_detail', None)

        context = {
            'user': user,
            'a_name': a_name,
            'a_email': a_email,
            'a_phone': a_phone,
            'a_interbank_account': a_interbank_account,
            'a_interbank_account_id': a_interbank_account_id,
            'ach_accountNumber': ach_accountNumber,
            'ach_routingNumber': ach_routingNumber,
            'ach_accountType': ach_accountType,
            'ach_bankName': ach_bankName,
            'wire_accountNumber': wire_accountNumber,
            'wire_routingNumber': wire_routingNumber,
            'wire_accountType': wire_accountType,
            'wire_bankName': wire_bankName,
            'wire_addressType': wire_addressType,
            'wire_line1': wire_line1,
            'wire_line2': wire_line2,
            'wire_city': wire_city,
            'wire_state': wire_state,
            'wire_zip': wire_zip,
            'wire_country': wire_country,
            'check_addressType': check_addressType,
            'check_line1': check_line1,
            'check_line2': check_line2,
            'check_city': check_city,
            'check_state': check_state,
            'check_zip': check_zip,
            'check_country': check_country,
            'card_addressType': card_addressType,
            'card_line1': card_line1,
            'card_line2': card_line2,
            'card_city': card_city,
            'card_state': card_state,
            'card_zip': card_zip,
            'card_country': card_country,
            'contact':contact
         }

        if show_ach_detail != None:
            return render(request, 'edit_contact_detail_ach.html', context)
        if show_wire_detail != None:
            return render(request, 'edit_contact_detail_wire.html', context)
        if show_wire_detail_address != None:
            return render(request, 'edit_contact_detail_wire_address.html', context)
        if show_check_detail != None:
            return render(request, 'edit_contact_detail_check.html', context)
        if show_card_detail != None:
            return render(request, 'edit_contact_detail_card.html', context)

        payload = {
            "accountId": account_id,
            "name": a_name,
            "email": a_email,
            "phone": a_phone
        }
        # Check if ach_accountNumber is not empty before including the "ach" section
        if a_interbank_account != '':
            payload["intrabank"] = {
                "accountNumber": a_interbank_account,
                "accountId": a_interbank_account_id
            }

        # Check if ach_accountNumber is not empty before including the "ach" section
        if ach_accountNumber != '':
            payload["ach"] = {
                "accountNumber": ach_accountNumber,
                "routingNumber": ach_routingNumber,
                "accountType": ach_accountType,
                "bankName": ach_bankName
            }

        # Include the "wire" section, assuming it's always included
        if wire_accountNumber != '':
            payload["wire"] = {
                "domestic": {
                    "accountNumber": wire_accountNumber,
                    "routingNumber": wire_routingNumber,
                    "accountType": wire_accountType,
                    "bankName": wire_bankName,
                    "address": {
                        "addressType": wire_addressType,
                        "line1": wire_line1,
                        "line2": wire_line2,
                        "city": wire_city,
                        "state": wire_state,
                        "country": wire_country,
                        "postalCode": wire_zip
                    }
                }
            }

        # Include the "check" section, assuming it's always included
        if check_line1 != '':
            payload["check"] = {
                "address": {
                    "addressType": check_addressType,
                    "line1": check_line1,
                    "line2": check_line2,
                    "city": check_city,
                    "state": check_state,
                    "country": check_country,
                    "postalCode": check_zip
                }
            }

        # Include the "card" section, assuming it's always included
        if card_line1 != '':
            payload["card"] = {
                "address": {
                    "addressType": card_addressType,
                    "line1": card_line1,
                    "line2": card_line2,
                    "city": card_city,
                    "state": card_state,
                    "country": card_country,
                    "postalCode": card_zip
                }
            }

        # Make the POST request
        responseapi = requests.patch(f"{base_url}/contact/{contact_id}", json=payload, headers=headers)

        # Check the response
        if responseapi.status_code == 200:
            data = responseapi.json()
            print("Contact created successfully:")
            print("Contact ID:", data["id"])
            print("Account ID:", data["accountId"])
            return redirect("get_contacts")
            # ... other fields you want to print
        else:
            print("Failed to create contact. Status code:", responseapi.status_code)
            print("Response content:", responseapi.content)

    context = {
        'user': user,
        'contact': contact
    }
    return render(request, 'edit_contact.html', context)

@login_required
def delete_contact(request):
    print("Entering my_profile function")

    user = request.user
    contact_id = request.GET.get('contact_id', '')

    api_key = os.environ.get('SOLIDFI')
    person_id = user.solidfi  # Replace with the actual person ID

    account_id = request.GET.get('account_id', user.active_bank_acc_id)

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }

    # Define the API endpoint URL
    url = "https://test-api.solidfi.com/v1/contact"  # Replace with the actual endpoint URL

    # Define the contact ID you want to delete

    # Make the DELETE request
    response = requests.delete(f"{url}/{contact_id}", headers=headers)

    # Check the response status code
    if response.status_code == 200:
        print("Contact removed successfully.")
    elif response.status_code == 404:
        print("Contact not found.")

    else:
        print(f"Failed to remove contact. Status code: {response.status_code}")


    return redirect("get_contacts")

@login_required
def add_contact(request):
    print("Entering my_profile function")

    user = request.user

    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1"
    person_id = user.solidfi  # Replace with the actual person ID

    account_id = request.GET.get('account_id', user.active_bank_acc_id)

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }
    if request.method == 'POST':
        account_id = user.active_bank_acc_id
        a_name = request.POST.get('name', '')
        a_email = request.POST.get('email', '')
        a_phone = request.POST.get('phone', '')
        a_interbank_account = request.POST.get('intrabank_account', '')
        a_interbank_account_id = request.POST.get('intrabank_account_id', '')
        ach_accountNumber = request.POST.get('ach_accountNumber', '')
        ach_routingNumber = request.POST.get('ach_routingNumber', '')
        ach_accountType = request.POST.get('ach_accountType', '')
        ach_bankName = request.POST.get('ach_bankName', '')
        wire_accountNumber = request.POST.get('wire_accountNumber', '')
        wire_routingNumber = request.POST.get('wire_routingNumber', '')
        wire_accountType = request.POST.get('wire_accountType', '')
        wire_bankName = request.POST.get('wire_bankName', '')
        wire_addressType = request.POST.get('wire_addressType', '')
        wire_line1 = request.POST.get('wire_line1', '')
        wire_line2 = request.POST.get('wire_line2', '')
        wire_city = request.POST.get('wire_city', '')
        wire_state = request.POST.get('wire_state', '')
        wire_country = request.POST.get('wire_country', '')
        wire_zip = request.POST.get('wire_zip', '')
        check_addressType = request.POST.get('check_addressType', '')
        check_line1 = request.POST.get('check_line1', '')
        check_line2 = request.POST.get('check_line2', '')
        check_city = request.POST.get('check_city', '')
        check_state = request.POST.get('check_state', '')
        check_country = request.POST.get('check_country', '')
        check_zip = request.POST.get('check_zip', '')
        card_addressType = request.POST.get('card_addressType', '')
        card_line1 = request.POST.get('card_line1', '')
        card_line2 = request.POST.get('card_line2', '')
        card_city = request.POST.get('card_city', '')
        card_state = request.POST.get('card_state', '')
        card_country = request.POST.get('card_country', '')
        card_zip = request.POST.get('card_zip', '')
        show_ach_detail = request.POST.get('show_ach_detail', None)
        show_wire_detail = request.POST.get('show_wire_detail', None)
        show_wire_detail_address = request.POST.get('show_wire_detail_address', None)
        show_check_detail = request.POST.get('show_check_detail', None)
        show_card_detail = request.POST.get('show_card_detail', None)

        context = {
            'user': user,
            'a_name': a_name,
            'a_email': a_email,
            'a_phone': a_phone,
            'a_interbank_account': a_interbank_account,
            'a_interbank_account_id': a_interbank_account_id,
            'ach_accountNumber': ach_accountNumber,
            'ach_routingNumber': ach_routingNumber,
            'ach_accountType': ach_accountType,
            'ach_bankName': ach_bankName,
            'wire_accountNumber': wire_accountNumber,
            'wire_routingNumber': wire_routingNumber,
            'wire_accountType': wire_accountType,
            'wire_bankName': wire_bankName,
            'wire_addressType': wire_addressType,
            'wire_line1': wire_line1,
            'wire_line2': wire_line2,
            'wire_city': wire_city,
            'wire_state': wire_state,
            'wire_zip': wire_zip,
            'wire_country': wire_country,
            'check_addressType': check_addressType,
            'check_line1': check_line1,
            'check_line2': check_line2,
            'check_city': check_city,
            'check_state': check_state,
            'check_zip': check_zip,
            'check_country': check_country,
            'card_addressType': card_addressType,
            'card_line1': card_line1,
            'card_line2': card_line2,
            'card_city': card_city,
            'card_state': card_state,
            'card_zip': card_zip,
            'card_country': card_country,
         }

        if show_ach_detail != None:
            return render(request, 'add_contact_detail_ach.html', context)
        if show_wire_detail != None:
            return render(request, 'add_contact_detail_wire.html', context)
        if show_wire_detail_address != None:
            return render(request, 'add_contact_detail_wire_address.html', context)
        if show_check_detail != None:
            return render(request, 'add_contact_detail_check.html', context)
        if show_card_detail != None:
            return render(request, 'add_contact_detail_card.html', context)

        print("Account ID:", account_id)
        print("Account ID:", a_interbank_account_id)

        payload = {
            "accountId": account_id,
            "name": a_name,
            "email": a_email,
            "phone": a_phone
        }
        # Check if ach_accountNumber is not empty before including the "ach" section
        if a_interbank_account != '':
            payload["intrabank"] = {
                "accountNumber": a_interbank_account,
                "accountId": a_interbank_account_id
            }

        # Check if ach_accountNumber is not empty before including the "ach" section
        if ach_accountNumber != '':
            payload["ach"] = {
                "accountNumber": ach_accountNumber,
                "routingNumber": ach_routingNumber,
                "accountType": ach_accountType,
                "bankName": ach_bankName
            }

        # Include the "wire" section, assuming it's always included
        if wire_accountNumber != '':
            payload["wire"] = {
                "domestic": {
                    "accountNumber": wire_accountNumber,
                    "routingNumber": wire_routingNumber,
                    "accountType": wire_accountType,
                    "bankName": wire_bankName,
                    "address": {
                        "addressType": wire_addressType,
                        "line1": wire_line1,
                        "line2": wire_line2,
                        "city": wire_city,
                        "state": wire_state,
                        "country": wire_country,
                        "postalCode": wire_zip
                    }
                }
            }

        # Include the "check" section, assuming it's always included
        if check_line1 != '':
            payload["check"] = {
                "address": {
                    "addressType": check_addressType,
                    "line1": check_line1,
                    "line2": check_line2,
                    "city": check_city,
                    "state": check_state,
                    "country": check_country,
                    "postalCode": check_zip
                }
            }

        # Include the "card" section, assuming it's always included
        if card_line1 != '':
            payload["card"] = {
                "address": {
                    "addressType": card_addressType,
                    "line1": card_line1,
                    "line2": card_line2,
                    "city": card_city,
                    "state": card_state,
                    "country": card_country,
                    "postalCode": card_zip
                }
            }

        # Make the POST request
        responseapi = requests.post(f"{base_url}/contact", json=payload, headers=headers)

        # Check the response
        if responseapi.status_code == 201:
            data = responseapi.json()
            print("Contact created successfully:")
            print("Contact ID:", data["id"])
            print("Account ID:", data["accountId"])
            return redirect("get_contacts")
            # ... other fields you want to print
        else:
            print("Failed to create contact. Status code:", responseapi.status_code)
            print("Response content:", responseapi.content)

    context = {
        'user': user
     }

    return render(request, 'add_contact.html', context)

@login_required
def send_check(request):
    user = request.user
    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1/send/check"
    person_id = user.solidfi  # Replace with the actual person ID

    contact_id = request.GET.get('contact_id')

    if request.method == 'POST':
        print("POST request detected")
        print("Profile form saved")
        # Extract form field values
        account_id = user.active_bank_acc_id
        amount = request.POST.get('amount')
        targetAccount = request.POST.get('targetAccount')
        description = request.POST.get('description', 'Not Provided')
        contact_id = targetAccount
        print("Account ID:", account_id)
        print("Amount:", amount)
        print("Target Account:", targetAccount)

        person_id = user.solidfi  # Replace with the actual person ID

        headers = {
            "Content-Type": "application/json",
            "sd-api-key": api_key,
            "sd-person-id": person_id
        }

        data = {
            "accountId": account_id,
            "contactId": targetAccount,
            "amount": amount,
            "description": description,
            "type": "physical"
        }
        print(data)
        response = requests.post(base_url, json=data, headers=headers)

        if response.status_code == 201:
            result = response.json()
            print("Transaction ID:", result["id"])
            print("Account ID:", result["accountId"])
            # Add more fields as needed
        else:
            print("Error:", response.status_code)
            print("Response:", response.text)

    context = {
        'user': user,
        'contact_id' : contact_id
     }
    return render(request, 'send_check.html', context)

@login_required
def send_domestic_wire(request):
    user = request.user
    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1/send/wire"
    person_id = user.solidfi  # Replace with the actual person ID

    contact_id = request.GET.get('contact_id')

    if request.method == 'POST':
        print("POST request detected")
        print("Profile form saved")
        # Extract form field values
        account_id = user.active_bank_acc_id
        amount = request.POST.get('amount')
        targetAccount = request.POST.get('targetAccount')
        description = request.POST.get('description', 'Not Provided')
        contact_id = targetAccount
        print("Account ID:", account_id)
        print("Amount:", amount)
        print("Target Account:", targetAccount)

        person_id = user.solidfi  # Replace with the actual person ID

        headers = {
            "Content-Type": "application/json",
            "sd-api-key": api_key,
            "sd-person-id": person_id
        }

        data = {
            "accountId": account_id,
            "contactId": targetAccount,
            "amount": amount,
            "description": description,
            "type": "domestic"
        }
        print(data)
        response = requests.post(base_url, json=data, headers=headers)

        if response.status_code == 201:
            result = response.json()
            print("Transaction ID:", result["id"])
            print("Account ID:", result["accountId"])
            # Add more fields as needed
        else:
            print("Error:", response.status_code)
            print("Response:", response.text)

    context = {
        'user': user,
        'contact_id' : contact_id
     }
    return render(request, 'send_domestic_wire.html', context)

@login_required
def send_ach(request):
    user = request.user
    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1/send/ach"
    person_id = user.solidfi  # Replace with the actual person ID

    contact_id = request.GET.get('contact_id')

    if request.method == 'POST':
        print("POST request detected")
        print("Profile form saved")
        # Extract form field values
        account_id = user.active_bank_acc_id
        amount = request.POST.get('amount')
        targetAccount = request.POST.get('targetAccount')
        description = request.POST.get('description', 'Not Provided')
        contact_id = targetAccount
        print("Account ID:", account_id)
        print("Amount:", amount)
        print("Target Account:", targetAccount)

        person_id = user.solidfi  # Replace with the actual person ID

        headers = {
            "Content-Type": "application/json",
            "sd-api-key": api_key,
            "sd-person-id": person_id
        }

        data = {
            "accountId": account_id,
            "contactId": targetAccount,
            "amount": amount,
            "description": description,
            "type": "sameDay"
        }
        print(data)
        response = requests.post(base_url, json=data, headers=headers)

        if response.status_code == 201:
            result = response.json()
            print("Transaction ID:", result["id"])
            print("Account ID:", result["accountId"])
            # Add more fields as needed
        else:
            print("Error:", response.status_code)
            print("Response:", response.text)
    context = {
        'user': user,
        'contact_id' : contact_id
     }
    return render(request, 'send_ach.html', context)

@login_required
def send_intrabank(request):

    user = request.user
    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1/send/intrabank"
    person_id = user.solidfi  # Replace with the actual person ID

    contact_id = request.GET.get('contact_id')

    if request.method == 'POST':
        print("POST request detected")
        print("Profile form saved")
        # Extract form field values
        account_id = user.active_bank_acc_id
        amount = request.POST.get('amount')
        targetAccount = request.POST.get('targetAccount')
        contact_id = targetAccount
        print("Account ID:", account_id)
        print("Amount:", amount)
        print("Target Account:", targetAccount)

        person_id = user.solidfi  # Replace with the actual person ID

        headers = {
            "Content-Type": "application/json",
            "sd-api-key": api_key,
            "sd-person-id": person_id
        }

        data = {
            "accountId": account_id,
            "contactId": targetAccount,
            "amount": amount,
            "description": "Funding"
        }
        print(data)
        response = requests.post(base_url, json=data, headers=headers)

        if response.status_code == 201:
            result = response.json()
            print("Transaction ID:", result["id"])
            print("Account ID:", result["accountId"])
            # Add more fields as needed
        else:
            print("Error:", response.status_code)
            print("Response:", response.text)


    context = {
        'user': user,
        'contact_id' : contact_id
     }
    return render(request, 'send_intrabank.html', context)

@login_required
def make_payment(request):
    print("Entering my_profile function")

    contact_id = request.GET.get('contact_id')
    user = request.user
    context = {
        'user': user,
        'contact_id' : contact_id
     }
    return render(request, 'make_payment.html', context)

@login_required
def contact_detail(request):
    print("Entering my_profile function")

    user = request.user
    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1"
    person_id = user.solidfi  # Replace with the actual person ID

    account_id = request.GET.get('account_id', user.active_bank_acc_id)

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }

    contact = None
    contact_id = request.GET.get('contact_id')

    api_url = f"{base_url}/contact/{contact_id}"
    try:
        response = requests.get(api_url, headers=headers)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            contact = response.json()

            # Print or process the data as needed
            print("Contact ID:", contact.get("id"))
            print("Name:", contact.get("name"))
            print("Email:", contact.get("email"))
            # Add more fields as needed

        else:
            print(f"Request failed with status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

    context = {
        'user': user,
        'contact': contact
     }
    return render(request, 'contact_detail.html', context)

@login_required
def get_contacts(request):
    print("Entering my_profile function")

    user = request.user

    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1"
    person_id = user.solidfi  # Replace with the actual person ID

    account_id = request.GET.get('account_id', user.active_bank_acc_id)
    search_key = None
    print("search_key called")
    if request.method == 'POST':
        print("search_key called POST")
        search_key = request.POST.get('search_key', None)
        print(search_key)

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }
    endpoint = "/contact"
    params = {
        "offset": 0,
        "limit": 25,
        "accountId": account_id
    }
    response = requests.get(base_url + endpoint, params=params, headers=headers)
    contact_list = None
    if response.status_code == 200:
        data = response.json()
        total_contacts = data["total"]
        contact_list = data["data"]
        print(f"Total contacts: {total_contacts}")

        if search_key is not None:
            # Filter the contact_list by contact names that contain the search_key (case-insensitive)
            contact_list = [contact for contact in contact_list if search_key.lower() in contact['name'].lower()]

        for contact in contact_list:
            print(f"Contact ID: {contact['id']}")
            print(f"Name: {contact['name']}")
            print(f"Email: {contact['email']}")
            print(f"Phone: {contact['phone']}")
            print("-" * 40)
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(f"Response content: {response.text}")

    context = {
        'user': user,
        'contact_list': contact_list
     }

    return render(request, 'get_contacts.html', context)

@login_required
def account_detail_first(request):
    print("Entering my_profile function")

    user = request.user

    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1"
    person_id = user.solidfi  # Replace with the actual person ID

    account_id = request.GET.get('account_id', user.active_bank_acc_id)

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }



    user.active_bank_acc_id = account_id
    user.save()


    account_data = None

    base_url = "https://test-api.solidfi.com/v1"
    endpoint = f"{base_url}/account/{account_id}"

    # Make the GET request
    response = requests.get(endpoint, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        account_data = response.json()  # The entire response is the account object

        # Display the desired data
        print("Account ID:", account_data["id"])
        print("Label:", account_data["label"])
        print("Routing Number:", account_data["routingNumber"])
        print("Account Number:", account_data["accountNumber"])
        print("Status:", account_data["status"])
        print("Type:", account_data["type"])
        print("Available Balance:", account_data["availableBalance"])
        print("Currency:", account_data["currency"])
        print("Created At:", account_data["createdAt"])
        print("Modified At:", account_data["modifiedAt"])
        print("Sponsor Bank Name:", account_data["sponsorBankName"])
        # ... Display other desired fields

    else:
        print("Error:", response.status_code)
        print("Response:", response.text)


    context = {
        'user': user,
        'account_id': account_id,
        'account_data': account_data
     }

    return render(request, 'account_detail_first.html', context)

@login_required
def account_detail(request):
    print("Entering my_profile function")

    user = request.user

    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1"
    person_id = user.solidfi  # Replace with the actual person ID

    account_id = request.GET.get('account_id', user.active_bank_acc_id)

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }

    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        a_name = request.POST.get('name')
        a_email = request.POST.get('email')
        a_phone = request.POST.get('phone')
        a_interbank_account = request.POST.get('intrabank_account')
        a_interbank_account_id = request.POST.get('intrabank_account_id')

        print("Account ID:", account_id)
        print("Account ID:", a_interbank_account_id)


        # Define the request payload
        payload = {
            "accountId": account_id,
            "name": a_name,
            "email": a_email,
            "phone": a_phone,
            "intrabank": {
                "accountId": a_interbank_account_id
            }
        }
        # Make the POST request
        responseapi = requests.post(f"{base_url}/contact", json=payload, headers=headers)

        # Check the response
        if responseapi.status_code == 201:
            data = responseapi.json()
            print("Contact created successfully:")
            print("Contact ID:", data["id"])
            print("Account ID:", data["accountId"])
            # ... other fields you want to print
        else:
            print("Failed to create contact. Status code:", responseapi.status_code)
            print("Response content:", responseapi.content)


    user.active_bank_acc_id = account_id
    user.save()

    endpoint = "/contact"
    params = {
        "offset": 0,
        "limit": 25,
        "accountId": account_id
    }
    response = requests.get(base_url + endpoint, params=params, headers=headers)
    contact_list = None
    if response.status_code == 200:
        data = response.json()
        total_contacts = data["total"]
        contact_list = data["data"]
        print(f"Total contacts: {total_contacts}")
        for contact in contact_list:
            print(f"Contact ID: {contact['id']}")
            print(f"Name: {contact['name']}")
            print(f"Email: {contact['email']}")
            print(f"Phone: {contact['phone']}")
            print("-" * 40)
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(f"Response content: {response.text}")
    contact_id = request.GET.get('contact_id')
    print(contact_id)
    print(contact_list)

    account_data = None

    base_url = "https://test-api.solidfi.com/v1"
    endpoint = f"{base_url}/account/{account_id}"

    # Make the GET request
    response = requests.get(endpoint, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        account_data = response.json()  # The entire response is the account object

        # Display the desired data
        print("Account ID:", account_data["id"])
        print("Label:", account_data["label"])
        print("Routing Number:", account_data["routingNumber"])
        print("Account Number:", account_data["accountNumber"])
        print("Status:", account_data["status"])
        print("Type:", account_data["type"])
        print("Available Balance:", account_data["availableBalance"])
        print("Currency:", account_data["currency"])
        print("Created At:", account_data["createdAt"])
        print("Modified At:", account_data["modifiedAt"])
        print("Sponsor Bank Name:", account_data["sponsorBankName"])
        # ... Display other desired fields

    else:
        print("Error:", response.status_code)
        print("Response:", response.text)

    send_money = request.GET.get('send_money', None)
    show_contacts = request.GET.get('show_contacts', None)
    show_add_contact = request.GET.get('show_add_contact', None)

    context = {
        'user': user,
        'account_id': account_id,
        'contact_id': contact_id,
        'contact_list': contact_list,
        'account_data': account_data,
        'send_money': send_money,
        'show_contacts': show_contacts,
        'show_add_contact': show_add_contact
     }

    return render(request, 'account_detail.html', context)

def add_spend(request):
    print("Entering my_profile function")

    user = request.user

    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com/v1/send/intrabank"
    person_id = user.solidfi  # Replace with the actual person ID


    if request.method == 'POST':
        print("POST request detected")
        print("Profile form saved")
        # Extract form field values
        account_id = request.POST.get('account_id')
        amount = request.POST.get('amount')
        targetAccount = request.POST.get('targetAccount')

        print("Account ID:", account_id)
        print("Amount:", amount)
        print("Target Account:", targetAccount)

        person_id = user.solidfi  # Replace with the actual person ID

        headers = {
            "Content-Type": "application/json",
            "sd-api-key": api_key,
            "sd-person-id": person_id
        }

        data = {
            "accountId": account_id,
            "contactId": targetAccount,
            "amount": amount,
            "description": "Funding"
        }
        print(data)
        response = requests.post(base_url, json=data, headers=headers)

        if response.status_code == 201:
            result = response.json()
            print("Transaction ID:", result["id"])
            print("Account ID:", result["accountId"])
            # Add more fields as needed
        else:
            print("Error:", response.status_code)
            print("Response:", response.text)


    return redirect(f"/account_detail/?account_id={account_id}")

@login_required
def add_first_bank_account_and_cc(request):
    print("Entering my_profile function")
    user = request.user

    if request.method == 'POST' and user.solidfi :

        api_key = os.environ.get('SOLIDFI')
        base_url = "https://test-api.solidfi.com"

        headers = {
            "Content-Type": "application/json",
            "sd-api-key": api_key,
            "sd-person-id": user.solidfi
        }

        # Example: Creating a Person
        create_person_url = f"{base_url}/v1/person"
        create_person_response = requests.post(create_person_url, headers=headers)
        create_person_data = create_person_response.json()
        created_person_id = create_person_data.get("personId")

        if created_person_id:
            print("Person created with ID:", created_person_id)
        else:
            print("Failed to create person.")

        # Example: Making a GET request using the created person ID
        get_person_url = f"{base_url}/v1/person"
        get_person_response = requests.get(get_person_url, headers=headers)
        get_person_data = get_person_response.json()

        print("Fetched person data:", get_person_data)

        # Access the 'idv' value
        idv_value = get_person_data['kyc']['results']['idv']

        if idv_value == 'notStarted':
            print("IDV Not Started")
            return redirect('add_idv')

        api_key = os.environ.get('SOLIDFI')
        base_url = "https://test-api.solidfi.com"
        person_id = user.solidfi  # Replace with the actual person ID

        headers = {
            "Content-Type": "application/json",
            "sd-api-key": api_key,
            "sd-person-id": person_id
        }

        api_url = "https://test-api.solidfi.com/v1/account"

        # Request data to submit a new IDV
        label = 'Primary'
        account_type = 'personalChecking'
        request_data = {
            "label": label,
            "acceptedTerms": True,
            "type": account_type
        }

        # Make the API request
        response = requests.post(f"{api_url}", json=request_data, headers=headers)

        # Check if the request was successful
        if response.status_code == 201:
            account_data = response.json()
            print("Account created successfully:")
            print("Account ID:", account_data["id"])
            print("Label:", account_data["label"])
            print("Type:", account_data["type"])
            a_id = account_data["id"]
            a_type = account_data["type"]
            a_label = account_data["label"]

            bank_account = BankAccount.objects.create(
                user=user,
                account_id=a_id,
                account_type=a_type,
                account_label=a_label
            )
            user.active_bank_acc_id=a_id
            user.save()
            bank_account.save()
            card_type = 'physical'
            if 'mail_card' in request.POST:
                checkbox_value = request.POST['mail_card']
                if checkbox_value == 'on':
                    # The checkbox is checked (True)
                    card_type = 'physical'
                else:
                    # The checkbox is unchecked (False)
                    card_type = 'virtual'
            else:
                # The checkbox was not in the form data, default to False
                card_type = 'virtual'
            #adding card
            card_type = request.POST.get('cardType', card_type)
            label = request.POST.get('label', 'Personal Card')
            currency = request.POST.get('currency', 'USD')
            limit_amount = request.POST.get('limitAmount', '1000.00')
            limit_interval = request.POST.get('limitInterval', 'allTime')

            billing_address_type = request.POST.get('billingAddressType', 'billing')
            billing_line1 = request.POST.get('billingLine1', user.billing_address_line1)
            billing_line2 = request.POST.get('billingLine2', user.billing_address_line1)
            billing_city = request.POST.get('billingCity', user.billing_city)
            billing_state = request.POST.get('billingState', user.billing_state)
            billing_country = request.POST.get('billingCountry', user.billing_country)
            billing_postal_code = request.POST.get('billingPostalCode', user.billing_zipcode)

            shipping_address_type = request.POST.get('shippingAddressType', 'shipping')
            shipping_line1 = request.POST.get('shippingLine1', user.billing_address_line1)
            shipping_line2 = request.POST.get('shippingLine2', user.billing_address_line2)
            shipping_city = request.POST.get('shippingCity', user.billing_city)
            shipping_state = request.POST.get('shippingState', user.billing_state)
            shipping_country = request.POST.get('shippingCountry', user.billing_country)
            shipping_postal_code = request.POST.get('shippingPostalCode', user.billing_zipcode)

            allowed_categories = request.POST.getlist('allowedCategories[]')

            bin_value = request.POST.get('bin', 'debit')

            if user.m_name :
                embossing_person_user = user.first_name + " " + user.m_name + ". " + user.last_name
            else :
                embossing_person_user = user.first_name + " " + user.last_name

            embossing_person = request.POST.get('embossingPerson', embossing_person_user)
            embossing_business = request.POST.get('embossingBusiness', '')

            payload = {
                "cardType": card_type,
                "label": label,
                "accountId": user.active_bank_acc_id,
                "currency": currency,
                "limitAmount": limit_amount,
                "limitInterval": limit_interval,
                "billingAddress": {
                    "addressType": billing_address_type,
                    "line1": billing_line1,
                    "line2": billing_line2,
                    "city": billing_city,
                    "state": billing_state,
                    "country": billing_country,
                    "postalCode": billing_postal_code
                },
                "shipping": {
                    "shippingAddress": {
                        "addressType": shipping_address_type,
                        "line1": shipping_line1,
                        "line2": shipping_line2,
                        "city": shipping_city,
                        "state": shipping_state,
                        "country": shipping_country,
                        "postalCode": shipping_postal_code
                    }
                },
                "allowedCategories": allowed_categories,
                "bin": bin_value,
                "embossingPerson": embossing_person,
                "embossingBusiness": embossing_business
            }

            # Set the URL for the POST request
            url = "https://test-api.solidfi.com/v1/card"

            # Make the POST request
            response = requests.post(url, json=payload, headers=headers)


            # Print the response
            print(response.json())

            # Add more fields as needed
        else:
            print("Account creation failed. Status code:", response.status_code)
            print("Response content:", response.text)

        return redirect('account_detail_first')

    context = {'user': user}
    return render(request, 'add_first_bank_account_and_cc.html', context)


@login_required
def add_bank_account(request):
    print("Entering my_profile function")
    user = request.user

    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com"
    person_id = user.solidfi  # Replace with the actual person ID

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }

    api_url = "https://test-api.solidfi.com/v1/account"

    # Request data to submit a new IDV
    label = request.POST.get('label', 'Primary')
    account_type = request.POST.get('account_type', 'personalChecking')
    request_data = {
        "label": label,
        "acceptedTerms": True,
        "type": account_type
    }

    # Make the API request
    response = requests.post(f"{api_url}", json=request_data, headers=headers)

    # Check if the request was successful
    if response.status_code == 201:
        account_data = response.json()
        print("Account created successfully:")
        print("Account ID:", account_data["id"])
        print("Label:", account_data["label"])
        print("Type:", account_data["type"])
        a_id = account_data["id"]
        a_type = account_data["type"]
        a_label = account_data["label"]

        bank_account = BankAccount.objects.create(
            user=user,
            account_id=a_id,
            account_type=a_type,
            account_label=a_label
        )
        user.save()
        bank_account.save()

        return redirect('my_profile_accounts')
        # Add more fields as needed
    else:
        print("Account creation failed. Status code:", response.status_code)
        print("Response content:", response.text)


    return redirect('my_profile')

@login_required
def add_card_first(request):
    user = request.user

    api_key = os.environ.get('SOLIDFI')
    person_id = user.solidfi  # Replace with the actual person ID

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }

    base_url = "https://test-api.solidfi.com/v1/card"
    # Define the query parameters for filtering the response
    query_params = {
        "offset": 0,
        "limit": 25,
        "accountId": user.active_bank_acc_id,  # Replace with your actual account ID
        "orderBy": "-createdAt"  # Order by createdAt in descending order
    }

    # Make the GET request
    response = requests.get(base_url, params=query_params, headers=headers)


    card = None
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json()

        total_cards = data["total"]
        cards = data["data"]

        print(f"Total cards: {total_cards}")
        for card in cards:
            card = card
            card_id = card["id"]
            card_type = card["cardType"]
            label = card["label"]
            limit_amount = card["limitAmount"]
            currency = card["currency"]
            last4 = card["last4"]
            card_status = card["cardStatus"]

            print(f"Card ID: {card_id}")
            print(f"Card Type: {card_type}")
            print(f"Label: {label}")
            print(f"Limit Amount: {limit_amount} {currency}")
            print(f"Last 4 Digits: {last4}")
            print(f"Card Status: {card_status}")
            print("------")
    else:
        print(f"Request failed with status code: {response.status_code}")

    context = {'user': user, 'card': card}
    return render(request, 'cc_detail_first.html', context)

@login_required
def get_card(request):
    user = request.user

    action = request.GET.get('action', 'None')
    api_key = os.environ.get('SOLIDFI')
    person_id = user.solidfi  # Replace with the actual person ID

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }

    if action == "activate" :
        print(request.GET.get('card_id'))
        card_id = request.GET.get('card_id')
        last4 = request.GET.get('last4')
        expiryMonth = request.GET.get('expiryMonth')
        expiryYear = request.GET.get('expiryYear')

        # Endpoint URL
        base_url = "https://test-api.solidfi.com"  # Replace with the actual base URL
        endpoint = f"{base_url}/v1/card/{card_id}/activate"

        # Request data
        request_data = {
            "expiryMonth": expiryMonth,
            "expiryYear": expiryYear,
            "last4": last4
        }

        # Send PATCH request
        response = requests.patch(endpoint, json=request_data, headers=headers)

        # Check response status code
        if response.status_code == 200:
            response_data = response.json()
            card_id = response_data["id"]
            card_status = response_data["status"]
            print(f"Card {card_id} is now {card_status}")
        else:
            print(f"Failed to activate card. Status code: {response.status_code}")


    base_url = "https://test-api.solidfi.com"

    card_id = request.GET.get('card_id')

    url = f"https://test-api.solidfi.com/v1/card/{card_id}"
    card_info = None
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            card_info = response.json()
            print("Card Information:")
            print(f"Card ID: {card_info['id']}")
            print(f"Cardholder Name: {card_info['cardholder']['name']}")
            print(f"Card Type: {card_info['cardType']}")
            print(f"Last 4 Digits: {card_info['last4']}")
            print(f"Expiry Date: {card_info['expiryMonth']}/{card_info['expiryYear']}")
            # Add more fields as needed
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

    context = {'user': user, 'card_info': card_info}
    return render(request, 'get_card.html', context)


@login_required
def add_card(request):
    user = request.user

    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com"
    person_id = user.solidfi  # Replace with the actual person ID

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }

    show_cards = request.GET.get('show_cards', 'False') == "True"

    if request.method == 'POST':
        # Define the request payload
        card_type = request.POST.get('cardType', 'physical')
        label = request.POST.get('label', 'Personal Card')
        currency = request.POST.get('currency', 'USD')
        limit_amount = request.POST.get('limitAmount', '1000.00')
        limit_interval = request.POST.get('limitInterval', 'allTime')

        billing_address_type = request.POST.get('billingAddressType', 'billing')
        billing_line1 = request.POST.get('billingLine1', user.billing_address_line1)
        billing_line2 = request.POST.get('billingLine2', '')
        billing_city = request.POST.get('billingCity', '')
        billing_state = request.POST.get('billingState', '')
        billing_country = request.POST.get('billingCountry', '')
        billing_postal_code = request.POST.get('billingPostalCode', '')

        shipping_address_type = request.POST.get('shippingAddressType', '')
        shipping_line1 = request.POST.get('shippingLine1', '')
        shipping_line2 = request.POST.get('shippingLine2', '')
        shipping_city = request.POST.get('shippingCity', '')
        shipping_state = request.POST.get('shippingState', '')
        shipping_country = request.POST.get('shippingCountry', '')
        shipping_postal_code = request.POST.get('shippingPostalCode', '')

        allowed_categories = request.POST.getlist('allowedCategories[]')

        bin_value = request.POST.get('bin', '')
        embossing_person = request.POST.get('embossingPerson', '')
        embossing_business = request.POST.get('embossingBusiness', '')

        payload = {
            "cardType": card_type,
            "label": label,
            "accountId": user.active_bank_acc_id,
            "currency": currency,
            "limitAmount": limit_amount,
            "limitInterval": limit_interval,
            "billingAddress": {
                "addressType": billing_address_type,
                "line1": billing_line1,
                "line2": billing_line2,
                "city": billing_city,
                "state": billing_state,
                "country": billing_country,
                "postalCode": billing_postal_code
            },
            "shipping": {
                "shippingAddress": {
                    "addressType": shipping_address_type,
                    "line1": shipping_line1,
                    "line2": shipping_line2,
                    "city": shipping_city,
                    "state": shipping_state,
                    "country": shipping_country,
                    "postalCode": shipping_postal_code
                }
            },
            "allowedCategories": allowed_categories,
            "bin": bin_value,
            "embossingPerson": embossing_person,
            "embossingBusiness": embossing_business
        }

        # Set the URL for the POST request
        url = "https://test-api.solidfi.com/v1/card"

        # Make the POST request
        response = requests.post(url, json=payload, headers=headers)

        # Print the response
        print(response.json())
        show_cards = True


    action = request.GET.get('action', 'None')

    if action == "activate" :
        print(request.GET.get('card_id'))
        card_id = request.GET.get('card_id')
        last4 = request.GET.get('last4')
        expiryMonth = request.GET.get('expiryMonth')
        expiryYear = request.GET.get('expiryYear')

        # Endpoint URL
        base_url = "https://test-api.solidfi.com"  # Replace with the actual base URL
        endpoint = f"{base_url}/v1/card/{card_id}/activate"

        # Request data
        request_data = {
            "expiryMonth": expiryMonth,
            "expiryYear": expiryYear,
            "last4": last4
        }

        # Send PATCH request
        response = requests.patch(endpoint, json=request_data, headers=headers)

        # Check response status code
        if response.status_code == 200:
            response_data = response.json()
            card_id = response_data["id"]
            card_status = response_data["status"]
            print(f"Card {card_id} is now {card_status}")
        else:
            print(f"Failed to activate card. Status code: {response.status_code}")

    base_url = "https://test-api.solidfi.com/v1/card"
    # Define the query parameters for filtering the response
    query_params = {
        "offset": 0,
        "limit": 25,
        "accountId": user.active_bank_acc_id,  # Replace with your actual account ID
        "orderBy": "-createdAt"  # Order by createdAt in descending order
    }

    # Make the GET request
    response = requests.get(base_url, params=query_params, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json()

        total_cards = data["total"]
        cards = data["data"]

        print(f"Total cards: {total_cards}")

        for card in cards:
            card_id = card["id"]
            card_type = card["cardType"]
            label = card["label"]
            limit_amount = card["limitAmount"]
            currency = card["currency"]
            last4 = card["last4"]
            card_status = card["cardStatus"]

            print(f"Card ID: {card_id}")
            print(f"Card Type: {card_type}")
            print(f"Label: {label}")
            print(f"Limit Amount: {limit_amount} {currency}")
            print(f"Last 4 Digits: {last4}")
            print(f"Card Status: {card_status}")
            print("------")
    else:
        print(f"Request failed with status code: {response.status_code}")

    context = {'user': user, 'cards': cards, 'show_cards': show_cards}
    return render(request, 'cc_detail.html', context)

'''
@login_required
def add_card_first(request):
    user = request.user

    api_key = os.environ.get('SOLIDFI')
    base_url = "https://test-api.solidfi.com"
    person_id = user.solidfi  # Replace with the actual person ID

    headers = {
        "Content-Type": "application/json",
        "sd-api-key": api_key,
        "sd-person-id": person_id
    }

    show_cards = request.GET.get('show_cards', 'False') == "True"



    action = request.GET.get('action', 'None')

    if action == "activate" :
        print(request.GET.get('card_id'))
        card_id = request.GET.get('card_id')
        last4 = request.GET.get('last4')
        expiryMonth = request.GET.get('expiryMonth')
        expiryYear = request.GET.get('expiryYear')

        # Endpoint URL
        base_url = "https://test-api.solidfi.com"  # Replace with the actual base URL
        endpoint = f"{base_url}/v1/card/{card_id}/activate"

        # Request data
        request_data = {
            "expiryMonth": expiryMonth,
            "expiryYear": expiryYear,
            "last4": last4
        }

        # Send PATCH request
        response = requests.patch(endpoint, json=request_data, headers=headers)

        # Check response status code
        if response.status_code == 200:
            response_data = response.json()
            card_id = response_data["id"]
            card_status = response_data["status"]
            print(f"Card {card_id} is now {card_status}")
        else:
            print(f"Failed to activate card. Status code: {response.status_code}")

    base_url = "https://test-api.solidfi.com/v1/card"
    # Define the query parameters for filtering the response
    query_params = {
        "offset": 0,
        "limit": 25,
        "accountId": user.active_bank_acc_id,  # Replace with your actual account ID
        "orderBy": "-createdAt"  # Order by createdAt in descending order
    }

    # Make the GET request
    response = requests.get(base_url, params=query_params, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json()

        total_cards = data["total"]
        cards = data["data"]

        print(f"Total cards: {total_cards}")

        for card in cards:
            card_id = card["id"]
            card_type = card["cardType"]
            label = card["label"]
            limit_amount = card["limitAmount"]
            currency = card["currency"]
            last4 = card["last4"]
            card_status = card["cardStatus"]

            print(f"Card ID: {card_id}")
            print(f"Card Type: {card_type}")
            print(f"Label: {label}")
            print(f"Limit Amount: {limit_amount} {currency}")
            print(f"Last 4 Digits: {last4}")
            print(f"Card Status: {card_status}")
            print("------")
    else:
        print(f"Request failed with status code: {response.status_code}")

    context = {'user': user, 'cards': cards, 'show_cards': show_cards}
    return render(request, 'cc_detail.html', context)
'''

@login_required
def pay_with_stripe(request):

    stripe.api_key = os.environ.get('STRIPE_KEY')

    cart_id = request.COOKIES.get('cartId')

    total = 10

    total_in_cents = int(total * 100)

    if request.method == 'POST':
        card_id = request.POST.get('stripeToken')
        try:
            charge = stripe.Charge.create(
                amount=total_in_cents,  # Amount in cents
                currency="usd",
                source=card_id,
                description="Example charge"
            )
        except stripe.error.CardError as e:
            # Handle error
            return redirect('failure')

        if charge.paid:
            print("Accounting is funded for $10")
            user = request.user
            api_key = os.environ.get('SOLIDFI')
            base_url = "https://test-api.solidfi.com/v1"
            person_id = os.environ.get('SOLIDFI_FUND_PER')
            account_id = os.environ.get('SOLIDFI_FUND_ACC')
            a_interbank_account_id = user.active_bank_acc_id

            targetAccount = 'NA'
            headers = {
                "Content-Type": "application/json",
                "sd-api-key": api_key,
                "sd-person-id": person_id
            }

            filters = {
                "externalId": a_interbank_account_id,
                "limit": 25,
                "offset": 0,
                "accountId": account_id
            }

            BASE_URL_C = "https://test-api.solidfi.com/v1/contact"
            responseCon = requests.get(BASE_URL_C, params=filters, headers=headers)

            if responseCon.status_code == 200:
                contacts_data = responseCon.json()
                if contacts_data:
                    total_contacts = contacts_data.get("total", 0)
                    contacts = contacts_data.get("data", [])

                    print(f"Total Contacts: {total_contacts}")
                    for contact in contacts:
                        print("Contact Details:")
                        print(f"ID: {contact['id']}")
                        print(f"Name: {contact['name']}")
                        print(f"Email: {contact['email']}")
                        print(f"Phone: {contact['phone']}")
                        print(f"Status: {contact['status']}")
                        # ... Add more fields as needed
                        targetAccount =f"{contact['id']}"
                else:
                    print("No contacts found.")
            else:
                print(f"Error: {responseCon.status_code}")




            a_name = user.first_name
            a_email = user.email
            a_phone = user.phone

            if targetAccount == 'NA':
                payload = {
                    "accountId": account_id,
                    "name": a_name,
                    "email": a_email,
                    "phone": a_phone,
                    "intrabank": {
                        "accountId": a_interbank_account_id
                    },
                    "metadata": {
                        "externalId": a_interbank_account_id,
                        "description": "Pro user"
                    }
                }
                # Make the POST request
                responseapi = requests.post(f"{base_url}/contact", json=payload, headers=headers)


                # Check the response
                if responseapi.status_code == 201:
                    data = responseapi.json()
                    print("Contact created successfully:")
                    print("Contact ID:", data["id"])
                    print("Account ID:", data["accountId"])
                    targetAccount = data["id"]
                    # ... other fields you want to print
                else:
                    print("Failed to create contact. Status code:", responseapi.status_code)
                    print("Response content:", responseapi.content)

            total_in_dollars = total_in_cents / 100.0
            amount = "{:.2f}".format(total_in_dollars)
            print("Account ID:", account_id)
            print("Amount:", amount)
            print("Target Account:", targetAccount)

            data = {
                "accountId": account_id,
                "contactId": targetAccount,
                "amount": amount,
                "description": "Funding"
            }
            print(data)
            base_url = "https://test-api.solidfi.com/v1/send/intrabank"
            response = requests.post(base_url, json=data, headers=headers)

            if response.status_code == 201:
                result = response.json()
                print("Transaction ID:", result["id"])
                print("Account ID:", result["accountId"])
                # Add more fields as needed
            else:
                print("Error:", response.status_code)
                print("Response:", response.text)


            response = redirect('success')
            response.delete_cookie("cartId")
            return response
        else:
            return redirect('failure')
    else:
        int(total * 100)
        context = {'total': total, 'total_in_cents': total_in_cents}
        return render(request, 'pay_with_stripe.html', context)

def generate_qr_codes(request):
    url = "https://api.browniecoins.org/getnewaddress.jsp"

    try:
        response = requests.get(url)
        address = ""
        privkey = ""

        if response.status_code == 200:
            address = response.text.strip()

            # Create a QR code for the address
            address_qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            address_qr.add_data(address)
            address_qr.make(fit=True)
            address_qr_img = address_qr.make_image(fill_color="black", back_color="white")

            url = "https://api.browniecoins.org/dumpprivkey.jsp?privkey=" + address
            response = requests.get(url)

            if response.status_code == 200:
                privkey = response.text.strip()

                # Create a QR code for the private key
                privkey_qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                privkey_qr.add_data(privkey)
                privkey_qr.make(fit=True)
                privkey_qr_img = privkey_qr.make_image(fill_color="black", back_color="white")

                # Create a blank image to combine the QR codes side by side
                combined_width = address_qr_img.size[0] + privkey_qr_img.size[0]
                combined_height = max(address_qr_img.size[1], privkey_qr_img.size[1])
                combined_image = Image.new("RGB", (combined_width, combined_height), "white")

                # Paste the address QR code on the left and private key QR code on the right
                combined_image.paste(address_qr_img, (0, 0))
                combined_image.paste(privkey_qr_img, (address_qr_img.size[0], 0))

                # Convert the combined image to bytes
                output_buffer = BytesIO()
                combined_image.save(output_buffer, format="PNG")
                image_data = output_buffer.getvalue()

                # Respond with the image as a URL
                response = HttpResponse(image_data, content_type="image/png")
                return response

            else:
                return HttpResponseBadRequest(f"Request failed with status code: {response.status_code}")

        else:
            return HttpResponseBadRequest(f"Request failed with status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        return HttpResponseBadRequest(f"An error occurred: {e}")

def get_magic_key_prize(request):
    tg_id = request.GET.get('tg_id')
    total_points = 1  # Initialize total points to zero

    if tg_id is not None and tg_id != 'h':
        # Query the MagicKey model to retrieve records where tg_id is not 'h' and magic_key is not equal to 'h', ordered by current_block
        magic_key_records = MagicKey.objects.filter(tg_id=tg_id).exclude(magic_key='h').order_by('current_block')

        for record in magic_key_records:
            # Compare magic_key_guess with magic_key
            if record.magic_key_guess == record.magic_key:
                total_points *= 16  # Increase by 16 for an exact match

            # Check if both characters are numeric
            if record.magic_key_guess.isdigit() and record.magic_key.isdigit():
                total_points *= 2

            # Check if both characters are alphabetic
            if record.magic_key_guess.isalpha() and record.magic_key.isalpha():
                total_points *= 3

        response_text = f'{total_points}'

        return HttpResponse(response_text)
    else:
        # Handle the case when tg_id is 'h' or not provided
        return HttpResponse('Invalid tg_id')

def add_magic_key(request):
    url = "https://api.browniecoins.org/getblockcount.jsp"
    response = requests.get(url)

    if response.status_code == 200:
        response_text = response.text
        current_block = response_text.strip()
        tg_id = request.GET.get('tg_id')
        magic_key_guess = request.GET.get('magic_key_guess')
        last_digit = 'h'  # Assuming you want to store the last digit of response_text

        # Check if a record with the same tg_id and current_block already exists
        existing_record = MagicKey.objects.filter(tg_id=tg_id, current_block=current_block).first()

        if existing_record:
            # Update the existing record
            existing_record.magic_key_guess = magic_key_guess
            existing_record.magic_key = last_digit
            existing_record.save()
            return HttpResponse("updated successfully.")

        else:
            # Create a new MagicKey instance and save it to the database
            magic_key_instance = MagicKey(
                tg_id=tg_id,
                current_block=current_block,
                magic_key_guess=magic_key_guess,
                magic_key=last_digit,
            )
            magic_key_instance.save()
            return HttpResponse("saved successfully.")

    else:
        print("Failed to retrieve data. Status code:", response.status_code)
        return HttpResponse("Failed to retrieve data. Status code: " + str(response.status_code), status=500)

def get_brownie_note(request):
    # URLs of the images
    url1 = "https://browniecoins.org/home/generate_qr_codes/"
    url2 = "https://browniecoins.org/home/static/images/100.png"

    # Download the images
    response1 = requests.get(url2)
    response2 = requests.get(url1)

    if response1.status_code == 200 and response2.status_code == 200:
        # Open and load the images using PIL
        image1 = Image.open(BytesIO(response1.content))
        image2 = Image.open(BytesIO(response2.content))

        new_width = image2.width // 4
        new_height = image2.height // 4

        # Resize image2
        image2 = image2.resize((new_width, new_height))

        # Ensure image2 is smaller than image1
        if image2.width < image1.width and image2.height < image1.height:
            # Define the position to paste image2 onto image1
            position = (25, 25)  # Adjust as needed

            # Paste image2 onto image1
            image1.paste(image2, position)

            # Create an in-memory response
            response = HttpResponse(content_type="image/png")
            image1.save(response, "PNG")
            return response
        else:
            return HttpResponse("Image 2 is not smaller than Image 1.")
    else:
        return HttpResponse("Failed to fetch one or both images. Check the URLs.")
