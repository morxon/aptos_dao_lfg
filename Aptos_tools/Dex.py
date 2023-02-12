import httpx
import time
from .Nft_work import Nft
from .config import tokens_for_swap
from aptos_sdk.bcs import Serializer
from aptos_sdk.client import RestClient, ApiError
from aptos_sdk.authenticator import Authenticator, Ed25519Authenticator
from aptos_sdk.transactions import TransactionPayload, SignedTransaction, RawTransaction, EntryFunction, \
    TransactionArgument
from aptos_sdk.type_tag import StructTag, TypeTag


class LiquidSwap(Nft):
    def __init__(self, node_url, account):
        super().__init__(node_url, account)
        self.aptos = RestClient(node_url)
        self.account = account

    @staticmethod
    async def get_price(token):
        async with httpx.AsyncClient() as session:
            return (await session.get("https://control.pontem.network/api/integrations"
                                      f"/fiat-prices?currencies={token.lower()}")).json()[0]['price']

    async def swap(self, token_from, token_to, amount_token_from):
        price_token_from, price_token_to = await self.get_price(token_from), await self.get_price(token_to)
        if token_from == "APT":
            give = int(amount_token_from * 10 ** 8)
            get = int((price_token_from/price_token_to * amount_token_from * 10**6) * 0.99)
        else:
            give = int(amount_token_from * 10 ** 6)
            get = int((price_token_from/price_token_to * amount_token_from * 10**8) * 0.99)
        raw_tx = RawTransaction(
            sender=self.account.account_address,
            sequence_number=self.aptos.account_sequence_number(self.account.account_address),
            payload=TransactionPayload(EntryFunction.natural(
                "0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12::scripts_v2",
                "swap",
                [TypeTag(StructTag.from_str(tokens_for_swap[token_from])),
                 TypeTag(StructTag.from_str(tokens_for_swap[token_to])),
                 TypeTag(StructTag.from_str("0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12::curves::Uncorrelated"))],
                [
                    TransactionArgument(give, Serializer.u64),
                    TransactionArgument(get, Serializer.u64),
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
