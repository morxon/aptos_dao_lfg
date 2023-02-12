from typing import List, Any
import httpx
import time
from aptos_sdk.bcs import Serializer
from aptos_sdk.client import RestClient, ApiError
from aptos_sdk.authenticator import Authenticator, Ed25519Authenticator
from aptos_sdk.transactions import TransactionPayload, SignedTransaction, RawTransaction, EntryFunction, \
    TransactionArgument


class Info:
    def __init__(self, node_url, account):
        self.aptos = httpx.AsyncClient(base_url=node_url)
        self.account = account

    async def get_all_nfts(self, result=None) -> List[Any]:
        result = [] if result is None else []
        handle_address = [log for log in (await self.aptos.get(
            f"accounts/{self.account.account_address}/resources")).json()
                          if log['type'] == "0x3::token::TokenStore"][0]['data']['tokens']['handle']
        resp = (await self.aptos.get(f"/accounts/{self.account.account_address}/events/0x3::token::TokenStore"
                                     f"/deposit_events"))
        if resp.status_code >= 400:
            raise ApiError(resp.text, resp.status_code)
        deposit_history = [log['data']['id'] for log in resp.json()]
        [deposit_history.remove(log) for log in deposit_history if deposit_history.count(log) > 1]
        for log in resp.json():
            property_version, token_data_id = log['data']['id']['property_version'], log['data']['id']['token_data_id']
            nft_info = await self.aptos.post(f"/tables/{handle_address}/item", json={
              "key_type": "0x3::token::TokenId",
              "value_type": "0x3::token::Token",
              "key": {
                "token_data_id": {
                  "collection": token_data_id["collection"],
                  "creator": token_data_id["creator"],
                  "name": token_data_id['name'],
                  "property_version": property_version,

                },
                "property_version": property_version
              }
            })
            if nft_info.status_code < 400:
                nft_info_resp = nft_info.json()['id']
                append_data = nft_info_resp['token_data_id']
                append_data.update({"property_version": nft_info_resp["property_version"]})
                result.append(append_data) if append_data not in result and nft_info.status_code < 400 else None
        return result

    async def get_all_tokens(self, result=None) -> list:
        result = [] if result is None else []
        resp = await self.aptos.get(f"/accounts/{self.account.account_address}/resources")
        if resp.status_code >= 400:
            raise ApiError(resp.text, resp.status_code)
        for log in resp.json():
            if "0x1::coin" in log['type']:
                result.append({log['type']: int(log["data"]["coin"]["value"]) / 10**8})
        return result

