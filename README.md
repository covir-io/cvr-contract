# COVIR token specifications

The goal of this document is to document all the features of the COVIR token implemented in the smart contract.

The aim of COVIR is to tokenize / digitalize the OctopusRobots licenses&#39; rights. The token holders will be eligible to 50% of the sale of licenses and 50% of the royalties from the sale of the robots.

## Glossary

_Owner: the wallet who published the smart contract_

_Administrator: wallet set as administrator in the smart contract by the owner_

_Sale Manager: the wallet allowed to create and sale tokens_

_Octopus: wallet owned by Octopus (the company owner of Licences)_

_Covir: wallet owned by Covir_

_Public function: any Tezos address can call the function_

_Private function: only the administrator address can call this function_

_Owner function: only the owner can call this function_

## Basic token settings &amp; functions

#### Token name: public function

This function returns the name of the token. The token name is &quot;COVIR&quot;.

#### Token symbol: public function

This function returns the symbol of the token. The symbol of the token is &quot;CVR&quot;.

#### Decimals: public function

This function returns the number of decimals of the token. The CVR token decimals is 6.

#### Token supply limit (_supplyLimit_): public function

This function returns the maximum number of tokens that can be minted by the smart contract. The maximum number of tokens to be minted over time is 400M.

#### Maximum sale token (_saleLimit_): public function

This function returns the maximum number of tokens to be sold by the sale function. The maximum number of tokens to be sold by the sale function is set to 200M. This value can be increased by the specific &quot;Increase available sale tokens&quot; function.

#### Circulating supply (c_irculatingSupply_): public function

This function returns the number of tokens in circulation, i.e. the total number of tokens already minted (and not burned).

#### Balance: public function

This function returns the balance in CVR of the given address.

#### Burn: public function

This function burns the tokens sent in parameters by the caller, i.e. an address can call the burn function to burn a given number of his own tokens.

Each time tokens are burned, the maximum token supply and the total supply decrease of the same amount.

#### Sold tokens (_soldToken_): public function

This function returns the number of tokens already sold.

## Administrator wallet management

The owner (and only the owner) of the contract can update/modify the administrator wallet address.

#### Default administrator address

A default administrator wallet address will be set at the initialization of the smart contract. If no other administrator wallet address has been set, this default address will be used as current administrator address.

#### Set administrator wallet address: owner function

This function updates the current administrator wallet address to be used by the smart contract with the one given in parameter.

#### Get current administrator wallet address: owner function

This function returns the current administrator wallet address (set by the previous function or the default one if no address has been set).

## Sale manager wallet management

The administrator of the contract can update/modify the sale manager wallet address.

#### Default sale manager address

A default sale manager wallet address will be set at the initialization of the smart contract.

#### Set sale manager wallet address: private function

This function updates the current sale manager wallet address to be used by the smart contract with the one given in parameter.

#### Get current sale manager wallet address: private function

This function returns the current sale manager wallet address (set by the previous function or the default one if no address has been set).

## Token transfer function

#### Transfer: public function

This function transfers a given number of tokens from the sender address to the given receiver address. The transfer of CVR tokens from one address to another can be processed if the Boolean &quot;transfer\_status&quot; is true and the sender address is not locked. Exception: the administrator wallet can transfer tokens even if the transfer status is false (for an airdrop for example).

The transfer function can be stopped during a period to prevent any token transfers between wallets (for example during an airdrop based on current balance of each wallet). The &quot;transfer\_status&quot; value is set to false by default (not allowed).

The transfer of tokens from a given address can be locked by the administrator. This feature can be useful for example if Covir.io wants to pay, in CVR, a company for marketing actions with a lock period. During this period, the tokens cannot be sent to another address or exchanged on the market. By default, the lock status is False for all addresses (transfer authorized).

A transfer can be processed only if the sender&#39;s balance is greater or equal to the amount to be transferred.

#### Lock transfer: private function

This function sets the boolean value &quot;transfer\_status&quot; to false.

Unlock transfer: private function

This function sets the boolean value &quot;transfer\_status&quot; to true.

#### Lock address: private function

This function sets the boolean value &quot;lock&quot; of the given address to true.

#### Unlock address: private function

This function sets the boolean value &quot;lock&quot; of the given address to false.

## Sale feature

#### Sale function: public function

The smart contract must include a sale feature for the token. The goal of this feature is to sell and send tokens against Tezos tokens.

This function must accept XTZ tokens and automatically sends back CVR tokens to the sender address according to the following exchange rate (see exchange rate section).

The sale will start when the contract will be published and will end when all the sale tokens (200M at the beginning) will be sold. A &quot;sale\_status&quot; Boolean variable will allow to pause and resume the sale if necessary. The &quot;sale\_status&quot; value is set to false by default (not allowed).

If the address is locked (see lock address function), the CVR must not be sent to the address and XTZ sent back to the address.

#### Admin sale function: private function

The smart contract also includes a sale feature for the administrator. The goal of this feature is to create and send tokens from the sale tokens pool without having to send XTZ to the smart contract. This function will be useful for the off-chain sale web platform (hosted at covir.io). This platform will manage the payment (in FIAT or other crypto) and call the smart contract to send the CVR tokens once payment will be validated.

This function accepts an amount and an address in parameters and automatically mints and sends the given amount of CVR tokens to the given address.

This function must succeed even if the &quot;sale\_status&quot; Boolean variable is False.

If the address is locked (see lock address function), the CVR must not be sent to the address and the function fails.

#### Exchange rate

The TEZOS / CVR exchange rate in this function is set to 1 XTZ = 1 CVR

#### XTZ distribution: private function

Only the administrator can run this function.

This function sends the the XTZ tokens received by the sale function, and held by the smart contract, according to the following rules: 25% sent to the Covir address; 75% sent to the Octopus address.

#### Sale ending condition

The sale function will be callable until the &quot;Maximum sale tokens&quot; is reached. If the number of sold tokens (&quot;sold\_tokens&quot; variable) has been reached, the sale function should fail and/or return a &quot;sale ended&quot; error message.

#### Pause sale: private function

This function sets the boolean value &quot;sale\_status&quot; to false. The sale feature is disabled / paused, and nobody can buy CVR tokens.

#### Resume sale: private function

This function sets the boolean value &quot;sale\_status&quot; to true. The sale feature is enabled / resumed.

#### Increase available sale tokens: private function

This function increases the number of token available for the sale function (Maximum sale tokens / _saleLimit_). The number of tokens to add to the sale limit is given in parameter.

The function must fail if the circulating supply + sale limit – sold tokens + given number is greater than the maximum total supply.

This function could be used when new types of licenses will be created and sold by Octopus to increase the number of tokens representing the licenses&#39; rights accordingly.

#### Get sold tokens: public function

This function returns the number of tokens already sold (_soldToken_).

## Token minting

All the tokens from maximum tokens for sale (initialized to 200M) to the maximum token supply (initialized to 400M), potentially 200M CVR, can be minted with the following function.

#### Mint tokens: private function

This function can mint new tokens (given number) and send them to the given address.

This function increases the circulating supply.

The function must fail if the circulating supply + sale limit – sold tokens + given number is greater than the maximum total supply.

## Airdrop function

As soon as the token smart contract is published, CVR tokens will be sent to Tezos tokens holders according to the following rules.

_Note: part of this feature will be processed off chain and will call an airdrop function, giving the number of tokens to send and the addresses._

#### Eligibility

All Tezos wallet with a balance of 100 XTZ minimum (at the time of contract publication) will receive CVR tokens airdrop.

#### Airdrop: private function

10 CVR tokens will be sent to all the wallets that meet the previous requirement (list of addresses built off chain and sent to airdrop function in parameters along with the amount to be sent to each address).

The airdrop function will call the Mint function, i.e. mint new token (not from sale tokens pool), and sends them to the given addresses.

## Royalties

This function will allow to send the Octopus licenses royalties to CVR tokens holders.

#### Send royalties: private function

This function will take the global amount of XTZ to send and the list of token holders addresses in parameters and sends XTZ to each address.

The number of XTZ to send to each address will be calculated according to the percentage of CVR tokens held by the address (regarding the circulating supply).

If the address is locked (see lock address function), the XTZ will be sent to the address.
