import httpx
import time
import asyncio
from .config import tokens_for_mint
from aptos_sdk.bcs import Serializer
from aptos_sdk.client import RestClient, ApiError
from aptos_sdk.authenticator import Authenticator, Ed25519Authenticator
from aptos_sdk.transactions import TransactionPayload, SignedTransaction, RawTransaction, EntryFunction,\
    TransactionArgument
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.type_tag import StructTag, TypeTag


class Nft:
    def __init__(self, node_url, account):
        self.aptos = RestClient(node_url)
        self.account = account

    async def send_tx(self, sign_transaction) -> str:
        async with httpx.AsyncClient(headers={"Content-Type": "application/x.aptos.signed_transaction+bcs"}) as client:
            response = await client.post(f"{self.aptos.base_url}/transactions", content=sign_transaction.bytes())
            if response.status_code >= 400:
                raise ApiError(response.text, response.status_code)
            return (response.json())["hash"]

    async def sell_blue_move(self, creator: str, collection: str, name: str, price: int, property_version):
        tx = self.aptos.submit_transaction(self.account, {
            "function": "0xd1fd99c1944b84d1670a2536417e997864ad12303d19eac725891691b04d614e::"
                        "marketplaceV2::batch_list_script",
            "type_arguments": [],
            "arguments": [
                [
                    creator
                ],
                [
                    collection,
                ],
                [
                    name,
                ],
                [
                    str(int(price * 10 ** 8)),
                ],
                [
                    str(property_version)
                ],
                        ],
            "type": "entry_function_payload"
        })

        return tx

    async def sell_topaz(self, creator: str, collection: str, name: str, price: int, property_version: int):
        raw_tx = RawTransaction(
            sender=self.account.account_address,
            sequence_number=self.aptos.account_sequence_number(self.account.account_address),
            payload=TransactionPayload(EntryFunction.natural(
                "0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2::marketplace_v2",
                "list",
                [TypeTag(StructTag.from_str("0x1::aptos_coin::AptosCoin"))],
                [
                    TransactionArgument(int(price * 10 ** 8), Serializer.u64),
                    TransactionArgument(1, Serializer.u64),
                    TransactionArgument(AccountAddress.from_hex(creator), Serializer.struct),
                    TransactionArgument(collection, Serializer.str),
                    TransactionArgument(name, Serializer.str),
                    TransactionArgument(property_version, Serializer.u64),
                ]
            )),
            max_gas_amount=9000,
            gas_unit_price=100,
            expiration_timestamps_secs=int(time.time()) + 600,
            chain_id=self.aptos.chain_id
        )
        signature = raw_tx.sign(self.account.private_key)
        authenticator = Authenticator(Ed25519Authenticator(self.account.public_key(), signature))
        sign_tx = SignedTransaction(raw_tx, authenticator)

        return await self.send_tx(sign_tx)


class BlueMove(Nft):
    def __init__(self, node_url, account, function, len_nft, gas_price, gas_amount, mint_time, token=None,
                 white_list=False):
        super().__init__(node_url, account)
        self.mint_time = mint_time
        self.token = token
        self.white_list = white_list
        self.sign_tx = self.create_tx(function, len_nft, gas_price, gas_amount)

    def create_tx(self, function: str, len_nft: int, gas_price: int, gas_amount: int):
        function_data = function.split('::')
        event = "mint_with_quantity" if self.white_list is False else "mint_with_quantity_wl"
        type_argument = [TypeTag(StructTag.from_str(tokens_for_mint[self.token]))] if self.token is not None else []

        payload = TransactionPayload(EntryFunction.natural(
            f"{function_data[0]}::{function_data[1]}",
            event,
            type_argument,
            [
                TransactionArgument(int(len_nft), Serializer.u64)
            ]))

        raw_tx = RawTransaction(
            sender=self.account.account_address,
            sequence_number=self.aptos.account_sequence_number(self.account.account_address),
            payload=payload,
            max_gas_amount=gas_amount,
            gas_unit_price=gas_price,
            expiration_timestamps_secs=int(time.time()) + 600,
            chain_id=self.aptos.chain_id
        )

        signature = raw_tx.sign(self.account.private_key)
        authenticator = Authenticator(Ed25519Authenticator(self.account.public_key(), signature))
        return SignedTransaction(raw_tx, authenticator)

    async def mint(self):
        if self.mint_time - time.time() > 0:
            await asyncio.sleep(self.mint_time - time.time())
            return await self.send_tx(self.sign_tx)
        else:
            print('mint end...')


class Topaz(Nft):
    def __init__(self, node_url, account, function, len_nft, gas_price, gas_amount, mint_time):
        super().__init__(node_url, account)
        self.mint_time = mint_time
        self.sign_tx = self.create_tx(function, len_nft, gas_price, gas_amount)

    def create_tx(self, function: str, len_nft: int, gas_price: int, gas_amount: int):
        function_data = function.split('::')
        event = "mint_with_quantity" if self.white_list is False else "mint_with_quantity_wl"
        type_argument = [TypeTag(StructTag.from_str(tokens_for_mint[self.token]))] if self.token is not None else []

        payload = TransactionPayload(EntryFunction.natural(
            f"{function_data[0]}::{function_data[1]}",
            event,
            type_argument,
            [
                TransactionArgument(int(len_nft), Serializer.u64)
            ]))

        raw_tx = RawTransaction(
            sender=self.account.account_address,
            sequence_number=self.aptos.account_sequence_number(self.account.account_address),
            payload=payload,
            max_gas_amount=gas_amount,
            gas_unit_price=gas_price,
            expiration_timestamps_secs=int(time.time()) + 600,
            chain_id=self.aptos.chain_id
        )

        signature = raw_tx.sign(self.account.private_key)
        authenticator = Authenticator(Ed25519Authenticator(self.account.public_key(), signature))
        return SignedTransaction(raw_tx, authenticator)

    async def mint(self):
        if self.mint_time - time.time() > 0:
            await asyncio.sleep(self.mint_time - time.time())
            return await self.send_tx(self.sign_tx)
        else:
            print('mint end...')

