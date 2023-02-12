import httpx
import time
from aptos_sdk.bcs import Serializer
from aptos_sdk.client import RestClient, ApiError
from aptos_sdk.authenticator import Authenticator, Ed25519Authenticator
from aptos_sdk.transactions import TransactionPayload, SignedTransaction, RawTransaction, EntryFunction, \
    TransactionArgument
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.type_tag import StructTag, TypeTag


class Transfers:
    def __init__(self, node_url, account_sender):
        self.aptos = RestClient(node_url)
        self.account_sender = account_sender

    async def from_to(self, amount: int, account_receiver) -> str:
        raw_tx = RawTransaction(
            sender=self.account_sender.account_address,
            sequence_number=self.aptos.account_sequence_number(self.account_sender.account_address),
            payload=TransactionPayload(EntryFunction.natural(
                "0x1::aptos_account",
                "transfer",
                [],
                [
                    TransactionArgument(account_receiver.account_address, Serializer.struct),
                    TransactionArgument(amount, Serializer.u64),
                ]
            )),
            max_gas_amount=3000,
            gas_unit_price=100,
            expiration_timestamps_secs=int(time.time()) + 600,
            chain_id=self.aptos.chain_id
        )

        signature = raw_tx.sign(self.account_sender.private_key)
        authenticator = Authenticator(Ed25519Authenticator(self.account_sender.public_key(), signature))
        sign_tx = SignedTransaction(raw_tx, authenticator)

        async with httpx.AsyncClient(headers={"Content-Type": "application/x.aptos.signed_transaction+bcs"}) as client:
            response = await client.post(f"{self.aptos.base_url}/transactions", content=sign_tx.bytes())
            if response.status_code >= 400:
                raise ApiError(response.text, response.status_code)
            return (response.json())["hash"]

