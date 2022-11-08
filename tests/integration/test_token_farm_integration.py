from brownie import network
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
)
import pytest
from scripts.deploy import deploy_punch_token_and_staking_farm


def test_stake_and_issue_correct_amounts(amount_staked):
    # Arrange
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Integration test only for local !")
    account = get_account()
    staking_farm, punch_token = deploy_punch_token_and_staking_farm()
    punch_token.approve(staking_farm.address, amount_staked, {"from": account})
    staking_farm.stakeTokens(punch_token.address, amount_staked, {"from": account})
    starting_balance = punch_token.balanceOf(account.address)
    price_feed_contract = get_contract("dai_usd_price_feed")
    (_, price, _, _, _) = price_feed_contract.latestRoundData()
    amount_token_to_issue = (
        price / 10 ** price_feed_contract.decimals()
    ) * amount_staked
    # Act
    issue_tx = staking_farm.issueTokens({"from": account})
    issue_tx.wait(1)
    # Assert
    assert (
        punch_token.balanceOf(account.address)
        == amount_token_to_issue + starting_balance
    )
