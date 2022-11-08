from web3 import Web3
from brownie import network, PunchToken, StakingFarm
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
)


KEPT_BALANCE = Web3.toWei(100, "ether")


def main():
    deploy_punch_token_and_staking_farm()


def deploy_punch_token_and_staking_farm():

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        account = get_account(index=0)
    elif network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        account = get_account()

    punch_token = PunchToken.deploy({"from": account})

    staking_farm = StakingFarm.deploy(punch_token.address, {"from": account})
    tx = punch_token.transfer(
        staking_farm.address,
        punch_token.totalSupply() - KEPT_BALANCE,
        {"from": account},
    )
    tx.wait(1)
    weth_token = get_contract("weth_token")
    fau_token = get_contract("fau_token")
    link_token = get_contract("link_token")
    add_allowed_tokens(
        staking_farm,
        {
            punch_token: get_contract("dai_usd_price_feed"),
            fau_token: get_contract("dai_usd_price_feed"),
            weth_token: get_contract("eth_usd_price_feed"),
            link_token: get_contract("link_usd_price_feed"),
        },
        account,
    )

    return staking_farm, punch_token


def add_allowed_tokens(staking_farm, _dic_of_allowed_tokens, account):
    for token in _dic_of_allowed_tokens:
        tx = staking_farm.addAllowedTokens(token, {"from": account})
        tx.wait(1)
        tx = staking_farm.setPriceFeedContract(
            token.address, _dic_of_allowed_tokens[token], {"from": account}
        )
        tx.wait(1)
