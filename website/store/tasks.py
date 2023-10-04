# myapp/tasks.py
from celery import Celery, shared_task
from django.db.models import Q

import json
import os

from .models import UserManager, BankAccount, PhoneVerification, TokenRecord, TokenBalance
from .forms import UserCreationForm, EditProfileForm
from web3 import Web3
#celery_app = Celery('store')
from django.db.models import Max, F
from django.db.models import Subquery, OuterRef
from collections import defaultdict

app = Celery('website')
@shared_task
def my_periodic_task_balance():

    # First, we'll create a subquery to get the latest updated_at timestamp for each token_id.
    latest_updated_at_subquery = TokenRecord.objects.filter(
        token_id=OuterRef('token_id')
    ).values('token_id').annotate(
        latest_updated_at=Max('updated_at')
    ).values('latest_updated_at')

    # Then, we'll use the subquery to filter the TokenRecord objects to get the latest record for each token_id.
    latest_records = TokenRecord.objects.annotate(
        latest_updated_at=Subquery(latest_updated_at_subquery)
    ).filter(
        updated_at=F('latest_updated_at')
    )

    for record in latest_records:
        # You can access the fields of each record like this
        contract_address = record.contract_address
        token_id = record.token_id
        token_owner = record.token_owner
        created_at = record.created_at
        updated_at = record.updated_at

        # Now you can do whatever you need with these values for each record
        print(f"Contract Address: {contract_address}")
        print(f"Token ID: {token_id}")
        print(f"Token Owner: {token_owner}")
        print(f"Created At: {created_at}")
        print(f"Updated At: {updated_at}")

    # Initialize a dictionary to store token owners and their associated token IDs
    token_owner_counts = defaultdict(list)

    for record in latest_records:
        token_owner = record.token_owner
        token_id = record.token_id

        # Append the token ID to the list associated with the token owner
        token_owner_counts[token_owner].append(token_id)

    # Initialize a dictionary to store the final result
    result = {}

    # Count the occurrences of each token ID for each token owner
    for token_owner, token_ids in token_owner_counts.items():
        token_id_count = len(token_ids)
        result[token_owner] = {
            'Token Owner': token_owner,
            'Token ID Count': token_id_count,
            'Token IDs': token_ids
        }

    # Print the result
    for token_owner, data in result.items():
        print(f"Token Owner: {data['Token Owner']}")
        print(f"Token ID Count: {data['Token ID Count']}")
        print(f"Token IDs: {data['Token IDs']}")
        print()
        contract_address = "0x0d2f8EE4194D79bBF4fee6c1f14ea5a0f5075b13"  # Replace with the actual ERC-20 contract address
        # Standard ERC-20 contract ABI for balance retrieval
        contract_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]

        infura_url = 'https://mainnet.infura.io/v3/' + os.environ.get('INFURA_KEY')
        w3_infura = Web3(Web3.HTTPProvider(infura_url))

        contract_infura = w3_infura.eth.contract(address=contract_address, abi=contract_abi)
        owner_address = data['Token Owner']
        token_balance_oc = contract_infura.functions.balanceOf(owner_address).call()
        token_balance = TokenBalance(
            contract_address_nft="0xD732789CDA5FCd978A26B3F58F658CD0885f8327",
            contract_address_erc20="0x0d2f8EE4194D79bBF4fee6c1f14ea5a0f5075b13",
            token_owner=data['Token Owner'],
            token_count=data['Token ID Count'],
            balance=token_balance_oc,
        )
        token_balance.save()

@shared_task
def my_periodic_task():
    # Your task logic goes here
    print("Scheduled Task Executed")
    infura = 'https://mainnet.infura.io/v3/' + os.environ.get('INFURA_KEY')
    w3 = Web3(Web3.HTTPProvider(infura))


    # Address of the ERC-721 contract
    contract_address = "0xD732789CDA5FCd978A26B3F58F658CD0885f8327"

    # ABI of the ERC-721 contract
    contract_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_tokenId", "type": "uint256"}],
            "name": "ownerOf",
            "outputs": [{"name": "owner", "type": "address"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
        # ... Add more function definitions as needed ...
    ]

    # Instantiate the contract
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    # Get the total supply of tokens
    total_supply = contract.functions.totalSupply().call()

        # Iterate through each token ID and retrieve the owner's address
    for token_id in range(total_supply):
        owner_address = contract.functions.ownerOf(token_id).call()
        token_record = TokenRecord(
            contract_address=contract_address,
            token_id=token_id,  # Replace with the appropriate token ID
            token_owner=owner_address
        )
        token_record.save()
        print("Scheduled Task Executed SAVED")


    pass
