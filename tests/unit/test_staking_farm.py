from scripts.helpful_scripts import (
    get_account,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_contract,
    INITIAL_PRICE_FEED_VALUE,
    DECIMALS,
)
from brownie import network, exceptions
import pytest
from scripts.deploy import deploy_punch_token_and_staking_farm, KEPT_BALANCE
from web3 import Web3


def test_set_token_price_feed_contract():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for Local testing !")
    account = get_account()
    non_owner = get_account(index=1)
    staking_farm, punch_token = deploy_punch_token_and_staking_farm()
    price_feed_address = get_contract("dai_usd_price_feed")
    # Act
    staking_farm.setPriceFeedContract(
        punch_token.address, price_feed_address, {"from": account}
    )
    # Assert

    assert staking_farm.tokenPriceFeedMapping(punch_token.address) == price_feed_address
    with pytest.raises(exceptions.VirtualMachineError):
        staking_farm.setPriceFeedContract(
            punch_token.address, price_feed_address, {"from": non_owner}
        )


def test_stake_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for Local testing !")
    account = get_account()
    staking_farm, punch_token = deploy_punch_token_and_staking_farm()
    token = punch_token.address
    # Act
    punch_token.approve(staking_farm.address, amount_staked, {"from": account})
    staking_farm.stakeTokens(token, amount_staked, {"from": account})
    # Assert
    assert staking_farm.stakingBalance(token, account) == amount_staked
    assert staking_farm.uniqueTokensStaked(account) == 1
    assert staking_farm.stakers(0) == account

    return staking_farm, punch_token


def test_issue_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for Local testing !")
    account = get_account()
    non_owner = get_account(index=1)
    staking_farm, punch_token = test_stake_tokens(amount_staked)
    starting_balance = punch_token.balanceOf(account.address)
    # Act
    staking_farm.issueTokens({"from": account})
    # Assert
    assert (
        punch_token.balanceOf(account.address)
        == starting_balance + INITIAL_PRICE_FEED_VALUE
    )
    with pytest.raises(exceptions.VirtualMachineError):
        staking_farm.issueTokens({"from": non_owner})


def test_get_user_total_value_with_different_tokens(amount_staked, random_erc20):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for Local testing !")
    account = get_account()
    staking_farm, punch_token = test_stake_tokens(amount_staked)
    # Act
    staking_farm.addAllowedTokens(random_erc20, {"from": account})
    staking_farm.setPriceFeedContract(
        random_erc20, get_contract("eth_usd_price_feed"), {"from": account}
    )
    random_erc20_staked_amount = amount_staked * 2
    random_erc20.approve(
        staking_farm.address, random_erc20_staked_amount, {"from": account}
    )
    staking_farm.stakeTokens(
        random_erc20, random_erc20_staked_amount, {"from": account}
    )
    # Assert
    total_value = staking_farm.getUserTotalValue(account.address)
    assert total_value == INITIAL_PRICE_FEED_VALUE * 3


def test_get_token_value():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for Local testing !")
    account = get_account()
    staking_farm, punch_token = deploy_punch_token_and_staking_farm()
    # Act / Assert
    assert staking_farm.getTokenValue(punch_token.address) == (
        INITIAL_PRICE_FEED_VALUE,
        DECIMALS,
    )


def test_unstake_tokens(amount_staked):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    staking_farm, punch_token = test_stake_tokens(amount_staked)
    # Act
    staking_farm.unstakeTokens(punch_token.address, {"from": account})
    assert punch_token.balanceOf(account.address) == KEPT_BALANCE
    assert staking_farm.stakingBalance(punch_token.address, account.address) == 0
    assert staking_farm.uniqueTokensStaked(account.address) == 0


def test_add_allowed_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")
    account = get_account()
    non_owner = get_account(index=1)
    staking_farm, punch_token = deploy_punch_token_and_staking_farm()
    # Act
    staking_farm.addAllowedTokens(punch_token.address, {"from": account})
    # Assert
    assert staking_farm.allowedTokens(0) == punch_token.address
    with pytest.raises(exceptions.VirtualMachineError):
        staking_farm.addAllowedTokens(punch_token.address, {"from": non_owner})


def test_token_is_allowed():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing!")

    staking_farm, punch_token = deploy_punch_token_and_staking_farm()

    # Assert
    assert staking_farm.isAllowed(punch_token.address) == True
