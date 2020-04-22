import smartpy as sp


class CVR(sp.Contract):
    def __init__(self, owner, admin, manager, octo, covir):
        self.init(factor=10**6, transferStatus=False, saleStatus=False, balances=sp.big_map(), owner=owner, administrator=admin, saleManager=manager, octopus=octo, covir=covir, circulatingSupply=0, saleLimit=200000000*10**6, supplyLimit=400000000*10**6, soldToken=0, tokenSymbol="CVR", tokenName="Covir", ratio=1)

    @sp.entry_point
    def transfer(self, params):
        sp.verify((sp.sender == self.data.administrator) | (self.data.transferStatus & (params.fromAddr == sp.sender)))
        sp.verify(self.data.balances.contains(params.fromAddr) & (~ self.data.balances[params.fromAddr].lock) & (self.data.balances[params.fromAddr].balance >= params.amount))
        sp.verify(params.amount > 0)
        self.addAddressIfNecessary(params.toAddr)
        self.data.balances[params.fromAddr].balance -= params.amount
        self.data.balances[params.toAddr].balance += params.amount
        
    def addAddressIfNecessary(self, address):
        sp.if ~ self.data.balances.contains(address):
            self.data.balances[address] = sp.record(balance=0, lock=False)

    @sp.entry_point
    def burn(self, params):
        sp.verify(params.fromAddr == sp.sender)
        sp.verify(self.data.balances.contains(params.fromAddr))
        sp.verify(self.data.balances[params.fromAddr].balance >= params.amount)
        self.data.balances[params.fromAddr].balance -= params.amount
        self.data.circulatingSupply -= params.amount
        self.data.supplyLimit -= params.amount

    @sp.entry_point
    def lockAddress(self, params):
        sp.verify(sp.sender == self.data.administrator)
        sp.verify(self.data.balances.contains(params.address))
        self.data.balances[params.address].lock = True

    @sp.entry_point
    def unlockAddress(self, params):
        sp.verify(sp.sender == self.data.administrator)
        sp.verify(self.data.balances.contains(params.address))
        self.data.balances[params.address].lock = False

    @sp.entry_point
    def pauseTransfer(self, params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.transferStatus = False

    @sp.entry_point
    def resumeTransfer(self, params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.transferStatus = True

    @sp.entry_point
    def pauseSale(self, params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.saleStatus = False

    @sp.entry_point
    def resumeSale(self, params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.saleStatus = True

    @sp.entry_point
    def setAdministrator(self, params):
        sp.verify(sp.sender == self.data.owner)
        self.addAddressIfNecessary(params)
        self.data.administrator = params

    @sp.entry_point
    def getAdministrator(self, params):
        sp.transfer(self.data.administrator, sp.tez(0), sp.contract(sp.TAddress, params.target).open_some())

    @sp.entry_point
    def setManager(self, params):
        sp.verify(sp.sender == self.data.administrator)
        self.addAddressIfNecessary(params)
        self.data.saleManager = params

    @sp.entry_point
    def getManager(self, params):
        sp.transfer(self.data.saleManager, sp.tez(0), sp.contract(sp.TAddress, params.target).open_some())

    @sp.entry_point
    def sale(self, params):
        sp.verify(self.data.saleStatus)
        sp.if self.data.balances.contains(sp.sender):
            sp.verify(~ self.data.balances[sp.sender].lock)
        natMutez = sp.fst(sp.ediv(sp.amount, sp.mutez(1)).open_some())
        intMutez = sp.to_int(natMutez)
        self.mintSale(sp.sender, intMutez * self.data.ratio)

    @sp.entry_point
    def offchainSale(self, params):
        sp.verify(sp.sender == self.data.saleManager)
        sp.if self.data.balances.contains(params.address):
            sp.verify(~ self.data.balances[params.address].lock)
        self.mintSale(params.address, params.amount)

    def mintSale(self, address, nbMutoken):
        sp.verify(self.data.soldToken + nbMutoken <= self.data.saleLimit)
        self.addAddressIfNecessary(address)
        self.data.balances[address].balance += nbMutoken
        self.data.circulatingSupply += nbMutoken
        self.data.soldToken += nbMutoken
    
    def checkLimit(self, amount):
        sp.verify(amount + self.data.saleLimit - self.data.soldToken + self.data.circulatingSupply <= self.data.supplyLimit)
    
    @sp.entry_point
    def mint(self, params):
        sp.verify(sp.sender == self.data.administrator)
        self.checkLimit(params.amount)
        self.addAddressIfNecessary(params.toAddr)
        self.data.balances[params.toAddr].balance += params.amount
        self.data.circulatingSupply += params.amount
   
    @sp.entry_point
    def increaseSaleLimit(self, params):
        sp.verify(sp.sender == self.data.administrator)
        self.checkLimit(params.amount)
        self.data.saleLimit += params.amount
        
    @sp.entry_point
    def cvrDrop(self, params):
        sp.verify(sp.sender == self.data.administrator)
        self.checkLimit(params.amount * sp.to_int(sp.len(params.addresses)))
        sp.for address in params.addresses:
            self.addAddressIfNecessary(address)
            self.data.balances[address].balance += params.amount
            self.data.circulatingSupply += params.amount
            
    @sp.entry_point
    def dispatchRoyalties(self, params):
        sp.verify(sp.sender == self.data.administrator)
        rounded = sp.as_nat(10**10)
        muCVRtez = sp.as_nat(self.data.circulatingSupply)*rounded // params.amount + 1
        sp.for address in params.addresses:
            sp.if (self.data.balances.contains(address) & (sp.as_nat(self.data.balances[address].balance)*rounded > muCVRtez)):
                sendMuTez = sp.as_nat(self.data.balances[address].balance)*rounded // muCVRtez
                sp.send(address, sp.mutez(sendMuTez))

    @sp.entry_point
    def claimSale(self, params):
        sp.verify(sp.sender == self.data.administrator)
        sp.verify(sp.balance > sp.mutez(params.amount))
        muSharetez = params.amount // 100
        self.processSplit(muSharetez)
   
    def processSplit(self, muSharetez):
        sp.send(self.data.octopus,  sp.mutez(muSharetez*75))
        sp.send(self.data.covir, sp.mutez(muSharetez*25))

    @sp.entry_point
    def getBalance(self, params):
        sp.if self.data.balances.contains(params.owner):
            sp.transfer(sp.as_nat(self.data.balances[params.owner].balance), sp.tez(0),
                        sp.contract(sp.TNat, params.target).open_some())
        sp.else:
            sp.transfer(sp.as_nat(0), sp.tez(0), sp.contract(sp.TNat, params.target).open_some())

    @sp.entry_point
    def getCirculatingSupply(self, params):
        sp.transfer(sp.as_nat(self.data.circulatingSupply), sp.tez(0), sp.contract(sp.TNat, params.target).open_some())

    @sp.entry_point
    def getSoldToken(self, params):
        sp.transfer(sp.as_nat(self.data.soldToken), sp.tez(0), sp.contract(sp.TNat, params.target).open_some())

    @sp.entry_point
    def getSaleLimit(self, params):
        sp.transfer(sp.as_nat(self.data.saleLimit), sp.tez(0), sp.contract(sp.TNat, params.target).open_some())

    @sp.entry_point
    def getSupplyLimit(self, params):
        sp.transfer(sp.as_nat(self.data.supplyLimit), sp.tez(0), sp.contract(sp.TNat, params.target).open_some())

    @sp.entry_point
    def getFactor(self, params):
        sp.transfer(sp.as_nat(self.data.factor), sp.tez(0), sp.contract(sp.TNat, params.target).open_some())
        
    @sp.entry_point
    def getTransferStatus(self, params):
        sp.if self.data.transferStatus:
            sp.transfer(1, sp.tez(0), sp.contract(sp.TNat, params.target).open_some())
        sp.else:
            sp.transfer(0, sp.tez(0), sp.contract(sp.TNat, params.target).open_some())
            
    @sp.entry_point
    def getSaleStatus(self, params):
        sp.if self.data.saleStatus:
            sp.transfer(1, sp.tez(0), sp.contract(sp.TNat, params.target).open_some())
        sp.else:
            sp.transfer(0, sp.tez(0), sp.contract(sp.TNat, params.target).open_some())


if "templates" not in __name__:
    @sp.add_test(name="CVR")
    def test():
        scenario = sp.test_scenario()
        scenario.h1("CVR Contract")
        
        owner = sp.address("tz1gVUyZjBWYckSfJN5VscLjVtDaiLmtoPnY")
        admin1 = sp.address("tz1fiqSBD4eXoquuFSfNqmfvnbJvUYSHd65c")
        admin2 = sp.address("tz1PAGGDfJchJNMayRkjxjKHoa76UCFwF7a6")
        manager1 = sp.address("tz1L5f3ZodeseeyuARJvya3WeHcorEdMhs3P")
        manager2 = sp.address("tz1fmptd1i9M6x4nXKE4qfo78Qqhg3t6B6Rd")
        octopus = sp.address("tz1aNuXU5LAkrcBr4zDa7ARoUsTYBbbmW53Q")
        covir = sp.address("tz1VCb95XH3jgyiQCrYF65DBAyujWbVSU2k8")
        
        alice = sp.address("tz1ToeY29e8EKsbnnTPrSWWMRKTpqcR5u9y5")
        bob = sp.address("tz1UVY6stBC9Zkr7B6a5BRJVbEWScSTbbjmd")
        jack = sp.address("tz1NgD3F7B3QDWzjLxLaSVAerzsghgDF5cPZ")
        johndoe1 = sp.address("tz1LcuQHNVQEWP2fZjk1QYZGNrfLDwrT3SyZ")
        johndoe2 = sp.address("tz1W5VkdB5s7ENMESVBtwyt9kyvLqPcUczRT")
        johndoe3 = sp.address("tz1RCFbB9GpALpsZtu6J58sb74dm8qe6XBzv")
        johndoe4 = sp.address("tz1WnfXMPaNTBmH7DBPwqCWs9cPDJdkGBTZ8")
        johndoe5 = sp.address("tz1LmaFsWRkjr7QMCx5PtV6xTUz3AmEpKQiF")
        johndoe6 = sp.address("tz1TNWtofRofCU11YwCNwTMWNFBodYi6eNqU")
        johndoe7 = sp.address("tz1LLNkQK4UQV6QcFShiXJ2vT2ELw449MzAA")
        johndoe8 = sp.address("tz1TDSmoZXwVevLTEvKCTHWpomG76oC9S2fJ")
        johndoe9 = sp.address("tz1PyxsQ7xVTa5J7gtBeT7pST5Zi5nk5GSjg")
        johndoe10 = sp.address("tz1PWCDnz783NNGGQjEFFsHtrcK5yBW4E2rm")
        johndoe11 = sp.address("tz3VEZ4k6a4Wx42iyev6i2aVAptTRLEAivNN")
        
        factor = 1000000

        c1 = CVR(owner, admin1, manager1, octopus, covir)
        scenario += c1
        
        
        ############################
        scenario.h2("Test init smart contract")
        
        scenario.h3("Get Factor")
        scenario += c1.getFactor(target=alice).run(sender=alice)
        
        scenario.h3("Get supply limit")
        scenario += c1.getSupplyLimit(target=alice).run(sender=alice)
        
        scenario.h3("Get sale limit")
        scenario += c1.getSaleLimit(target=alice).run(sender=alice)
        
        scenario.h3("Get circulating supply")
        scenario += c1.getCirculatingSupply(target=alice).run(sender=alice)
        
        scenario.h3("Alice gets balance of Alice")
        scenario += c1.getBalance(owner=alice, target=alice).run(sender=alice)
        
        scenario.h3("Bob gets balance of Alice")
        scenario += c1.getBalance(owner=alice, target=bob).run(sender=bob)
        
        scenario.h3("Get transfer status")
        scenario += c1.getTransferStatus(target=alice).run(sender=alice)
        
        scenario.h3("Get sale status")
        scenario += c1.getSaleStatus(target=alice).run(sender=alice)
        
        scenario.h3("Get number of sold tokens")
        scenario += c1.getSoldToken(target=alice).run(sender=alice)
        
        
        ########################
        scenario.h2("Test update admin")
        scenario.h3("Jack tries to set himself as administrator")
        scenario += c1.setAdministrator(jack).run(sender=jack, valid=False)
        
        scenario.h3("Get current administrator address")
        scenario += c1.getAdministrator(target=alice).run(sender=alice)
        
        scenario.h3("Admin1 tries to set admin2 as administrator")
        scenario += c1.setAdministrator(admin2).run(sender=admin1, valid=False)
        
        scenario.h3("Get current administrator address")
        scenario += c1.getAdministrator(target=alice).run(sender=alice)
        
        # test not available on smartpy
        # scenario.h3("Owner tries to set a wrong formated address as administrator")
        # scenario += c1.setAdministrator(sp.address("tz1LmaFsWRkjr7QMCx5")).run(sender=owner, valid=False)
        
        scenario.h3("Owner sets admin2 as administrator")
        scenario += c1.setAdministrator(admin2).run(sender=owner)
        
        scenario.h3("Get current administrator address")
        scenario += c1.getAdministrator(target=alice).run(sender=alice)
        
        
        #############################
        scenario.h2("Test airdrop feature")
        scenario.h3("Jack tries to aidrop tokens to himself")
        scenario += c1.cvrDrop(addresses=[jack], amount=100 * factor).run(sender=jack, valid=False)
        
        scenario.h3("Get circulating supply to verify that previous airdrop did not succeed")
        scenario += c1.getCirculatingSupply(target=alice).run(sender=alice)
        
        scenario.h3("Admin1 tries to aidrop tokens to Alice")
        scenario += c1.cvrDrop(addresses=[alice], amount=10 * factor).run(sender=admin1, valid=False)
        
        scenario.h3("Admin2 aidrop tokens to a list of one wallet: Alice")
        scenario += c1.cvrDrop(addresses=[alice], amount=10 * factor).run(sender=admin2)
        
        scenario.h3("Admin2 locks Alice's address")
        scenario += c1.lockAddress(address=alice).run(sender=admin2)
        
        scenario.h3("Admin2 aidrop tokens to a list wallets, including one lock address: Alice")
        scenario += c1.cvrDrop(addresses=[alice, bob, jack], amount=10 * factor).run(sender=admin2)
        
        scenario.h3("Admin2 aidrop too many tokens (over supply limit)")
        scenario += c1.cvrDrop(addresses=[alice, bob, jack], amount=200000000 * factor).run(sender=admin2, valid=False)
        
        scenario.h3("Admin2 unlocks Alice's address")
        scenario += c1.unlockAddress(address=alice).run(sender=admin2)
        
        scenario.h3("Alice gets balance of Alice")
        scenario += c1.getBalance(owner=alice, target=alice).run(sender=alice)
        
        scenario.h3("Bob gets balance of Bob")
        scenario += c1.getBalance(owner=bob, target=bob).run(sender=bob)
        
        scenario.h3("Jack gets balance of Jack")
        scenario += c1.getBalance(owner=jack, target=jack).run(sender=jack)
        
        scenario.h3("Get number of sold tokens")
        scenario += c1.getSoldToken(target=alice).run(sender=alice)
        
        scenario.h3("Get circulating supply")
        scenario += c1.getCirculatingSupply(target=alice).run(sender=alice)
        
        
        #############################
        scenario.h2("Test sale feature")
        scenario.h3("Alice tries to buy tokens but sale status is False")
        scenario += c1.sale().run(sender=alice, amount=sp.tez(1), valid=False)
        
        scenario.h3("Jack tries to increase the sale limit")
        scenario += c1.increaseSaleLimit(amount=1000000).run(sender=jack, valid=False)
        
        scenario.h3("Alice gets sale limit to verify that is has not changed")
        scenario += c1.getSaleLimit(target=alice).run(sender=alice)
        
        scenario.h3("Admin2 increases the sale limit by 2M")
        scenario += c1.increaseSaleLimit(amount=2000000 * factor).run(sender=admin2)
        
        scenario.h3("Alice gets sale limit to verify that is has been updated to 202M")
        scenario += c1.getSaleLimit(target=alice).run(sender=alice)
        
        scenario.h3("Jack tries to set sale status to True")
        scenario += c1.resumeSale().run(sender=jack, valid=False)
        
        scenario.h3("Jack tries to buy tokens but sale status is False, check that sale status is still False")
        scenario += c1.sale().run(sender=jack, amount=sp.tez(10), valid=False)
        
        scenario.h3("Admin2 resume sale = set sale status to True")
        scenario += c1.resumeSale().run(sender=admin2)
        
        scenario.h3("Alice gets sale status to verify it is True")
        scenario += c1.getSaleStatus(target=alice).run(sender=alice)
        
        scenario.h3("Alice buys 100 tokens with 100 tez")
        scenario += c1.sale().run(sender=alice, amount=sp.tez(100))
        
        scenario.h3("Bob buys 11,23 tokens with 11,23 tez")
        scenario += c1.sale().run(sender=alice, amount=sp.mutez(11230000))
        
        scenario.h3("Admin2 locks Bob's address")
        scenario += c1.lockAddress(address=bob).run(sender=admin2)
        
        scenario.h3("Bob tries to buy 100 tokens but Bob is locked")
        scenario += c1.sale().run(sender=bob, amount=sp.tez(100), valid=False)
        
        scenario.h3("Admin2 unlocks Bob's address")
        scenario += c1.unlockAddress(address=bob).run(sender=admin2)
        
        scenario.h3("Get number of sold tokens")
        scenario += c1.getSoldToken(target=alice).run(sender=alice)
        
        scenario.h3("Alice gets balance of Alice to verify she received tokens")
        scenario += c1.getBalance(owner=alice, target=alice).run(sender=alice)
        
        scenario.h3("Bob gets balance of Bob to verify he did not receive tokens")
        scenario += c1.getBalance(owner=bob, target=bob).run(sender=bob)
        
        scenario.h3("Verify circulating supply")
        scenario += c1.getCirculatingSupply(target=alice).run(sender=alice)
        
        scenario.h3("Jack tries to set sale status to False")
        scenario += c1.pauseSale().run(sender=jack, valid=False)
        
        scenario.h3("Alice gets sale status to verify it is still True")
        scenario += c1.getSaleStatus(target=alice).run(sender=alice)
        
        scenario.h3("Admin2 sets sale status to False")
        scenario += c1.pauseSale().run(sender=admin2)
        
        scenario.h3("Jack tries to buy tokens but sale status is False, check that sale status is False")
        scenario += c1.sale().run(sender=jack, amount=sp.tez(100), valid=False)
        
        scenario.h3("Jack tries to set himself as manager")
        scenario += c1.setManager(jack).run(sender=jack, valid=False)
        
        scenario.h3("Admin1 tries to set manager2 as sale manager")
        scenario += c1.setManager(manager2).run(sender=admin1, valid=False)
        
        scenario.h3("Manager1 tries to set manager2 as sale manager")
        scenario += c1.setManager(manager2).run(sender=manager1, valid=False)
        
        scenario.h3("Admin2 set manager2 as sale manager")
        scenario += c1.setManager(manager2).run(sender=admin2)
        
        scenario.h3("Get current manager address")
        scenario += c1.getManager(target=alice).run(sender=alice)
        
        scenario.h3("Jack tries to send sale tokens to jack")
        scenario += c1.offchainSale(address=jack, amount=1000000).run(sender=jack, valid=False)
        
        scenario.h3("Manager1 tries to send sale tokens to jack")
        scenario += c1.offchainSale(address=jack, amount=1000000).run(sender=manager1, valid=False)
        
        scenario.h3("Admin2 tries to send sale tokens to jack")
        scenario += c1.offchainSale(address=jack, amount=1000000).run(sender=admin2, valid=False)
        
        scenario.h3("Manager2 sales to Alice")
        scenario += c1.offchainSale(address=alice, amount=1000000000).run(sender=manager2)
        
        scenario.h3("Manager2 sales to Bob")
        scenario += c1.offchainSale(address=bob, amount=123456000).run(sender=manager2)
        
        scenario.h3("Get number of sold tokens")
        scenario += c1.getSoldToken(target=alice).run(sender=alice)
        
        scenario.h3("Jack launch 10 XTZ claim from sale")
        scenario += c1.claimSale(amount=10000000).run(sender=jack, valid=False)
        
        scenario.h3("Admin1 launch 10 XTZ claim from sale")
        scenario += c1.claimSale(amount=10000000).run(sender=admin1, valid=False)
        
        scenario.h3("Manager2 launch 10 XTZ claim from sale")
        scenario += c1.claimSale(amount=10000000).run(sender=manager2, valid=False)
        
        scenario.h3("Admin2 launch XTZ claim from sale")
        scenario += c1.claimSale(amount=10000000).run(sender=admin2)
        
        scenario.h3("Admin2 launch XTZ claim from sale")
        scenario += c1.claimSale(amount=12345000).run(sender=admin2)
        
        scenario.h3("Admin2 launch XTZ claim from sale, exceeding owner balance")
        scenario += c1.claimSale(amount=10000000000).run(sender=admin2, valid=False)
        
        scenario.h3("Admin2 tries to increase the sale limit by 200M tokens, exceeding the supply limit")
        scenario += c1.increaseSaleLimit(amount=200000000 * factor).run(sender=admin2, valid=False)
        
        scenario.h3("Alice gets sale limit to verify that it has not changed")
        scenario += c1.getSaleLimit(target=alice).run(sender=alice)
        
        
        #############################
        scenario.h2("Test transfer feature")
        scenario.h3("Jack tries to unlock transfer function")
        scenario += c1.resumeTransfer().run(sender=jack, valid=False)
        
        scenario.h3("Jack tries to transfer 1 token to Bob")
        scenario += c1.transfer(fromAddr=jack, toAddr=bob, amount=1 * factor).run(sender=jack, valid=False)
        
        scenario.h3("Admin2 tries to transfer 1 token to Bob, but balance = 0")
        scenario += c1.transfer(fromAddr=admin2, toAddr=bob, amount=1 * factor).run(sender=admin2, valid=False)
        
        scenario.h3("Admin2 unlock transfer function, set transfer status to True")
        scenario += c1.resumeTransfer().run(sender=admin2)
        
        scenario.h3("Alice gets the current transfer status to verify it is True")
        scenario += c1.getTransferStatus(target=alice).run(sender=alice)
        
        scenario.h3("Jack tries to transfer 10 token from Alice to Jack")
        scenario += c1.transfer(fromAddr=alice, toAddr=jack, amount=10 * factor).run(sender=jack, valid=False)
        
        scenario.h3("Alice transfers 10 token from Alice to Bob")
        scenario += c1.transfer(fromAddr=alice, toAddr=bob, amount=10 * factor).run(sender=alice)
        
        scenario.h3("Bob transfers 3.456 token from Bob to Alice")
        scenario += c1.transfer(fromAddr=bob, toAddr=alice, amount=3456000).run(sender=bob)
        
        scenario.h3("Jack tries to lock Bob address")
        scenario += c1.lockAddress(address=bob).run(sender=jack, valid=False)
        
        scenario.h3("Admin2 locks Jack address")
        scenario += c1.lockAddress(address=jack).run(sender=admin2)
        
        scenario.h3("Jack tries to transfer 10 tokens from Jack to Bob but jack is locked")
        scenario += c1.transfer(fromAddr=jack, toAddr=bob, amount=10 * factor).run(sender=jack, valid=False)
        
        scenario.h3("Admin2 locks Bob address")
        scenario += c1.lockAddress(address=bob).run(sender=admin2)
        
        scenario.h3("Bob tries to transfer 10 tokens from Bob to Alice but Bob is locked")
        scenario += c1.transfer(fromAddr=bob, toAddr=alice, amount=10 * factor).run(sender=bob, valid=False)
        
        scenario.h3("Alice transfers 10 tokens from Alice to Bob. It works even if Bob is locked")
        scenario += c1.transfer(fromAddr=alice, toAddr=bob, amount=10 * factor).run(sender=alice)
        
        scenario.h3("Jack tries to unlock Jack address")
        scenario += c1.unlockAddress(address=jack).run(sender=jack, valid=False)
        
        scenario.h3("Admin2 unlocks Bob address")
        scenario += c1.unlockAddress(address=bob).run(sender=admin2)
        
        scenario.h3("Alice transfers 10 tokens from Alice to Bob")
        scenario += c1.transfer(fromAddr=alice, toAddr=bob, amount=10 * factor).run(sender=alice)
        
        scenario.h3("Alice transfers 10 tokens from Alice to Alice")
        scenario += c1.transfer(fromAddr=alice, toAddr=alice, amount=10 * factor).run(sender=alice)
        
        # test not available on smartpy
        # scenario.h3("Alice transfers 10 tokens from Alice to bad format address")
        # scenario += c1.transfer(fromAddr=alice, toAddr="tz1LcuQHNVjk1QYZGNrf", amount=1 * factor).run(sender=alice, valid=False)
        
        scenario.h3("Jack tries to lock transfer function")
        scenario += c1.pauseTransfer().run(sender=jack, valid=False)
        
        scenario.h3("Admin2 locks transfer function")
        scenario += c1.pauseTransfer().run(sender=admin2)
        
        scenario.h3("Alice gets the current transfer status to verify it is False")
        scenario += c1.getTransferStatus(target=alice).run(sender=alice)
        
        scenario.h3("Alice transfers 10 token from Alice to Bob")
        scenario += c1.transfer(fromAddr=alice, toAddr=bob, amount=10 * factor).run(sender=alice, valid=False)
        
        
        #############################
        scenario.h2("Test burn feature")
        scenario.h3("Jack tries to burn 1000 tokens owned by Jack, but balance is less")
        scenario += c1.burn(fromAddr=jack, amount=1000 * factor).run(sender=jack, valid=False)
        
        scenario.h3("Jack tries to burn 10 tokens owned by Bob")
        scenario += c1.burn(fromAddr=bob, amount=10 * factor).run(sender=jack, valid=False)
        
        scenario.h3("Get circulating supply to verify nothing has been burned")
        scenario += c1.getCirculatingSupply(target=alice).run(sender=alice)
        
        scenario.h3("Get supply limit to verify nothing has been burned")
        scenario += c1.getSupplyLimit(target=alice).run(sender=alice)
        
        scenario.h3("Alice burns 10 tokens owned by Alice")
        scenario += c1.burn(fromAddr=alice, amount=10 * factor).run(sender=alice)
        
        scenario.h3("Bob burns 2.3456 tokens owned by Bob")
        scenario += c1.burn(fromAddr=bob, amount=2345600).run(sender=bob)
        
        scenario.h3("Alice gets balance of Alice to verify burned tokens")
        scenario += c1.getBalance(owner=alice, target=alice).run(sender=alice)
        
        scenario.h3("Bob gets balance of Bob to verify burned tokens")
        scenario += c1.getBalance(owner=bob, target=bob).run(sender=bob)
        
        scenario.h3("Get number of sold tokens to verify burn has no impact on sold tokens")
        scenario += c1.getSoldToken(target=alice).run(sender=alice)
        
        scenario.h3("Get circulating supply to verify it has been updated")
        scenario += c1.getCirculatingSupply(target=alice).run(sender=alice)
        
        scenario.h3("Get supply limit to verify it has been updated")
        scenario += c1.getSupplyLimit(target=alice).run(sender=alice)
        
        
        #############################
        scenario.h2("Test mint feature")
        scenario.h3("Jack tries to mint 1000 tokens to Jack")
        scenario += c1.mint(toAddr=jack, amount=1000 * factor).run(sender=jack, valid=False)
        
        scenario.h3("Get circulating supply to verify tokens have not been minted")
        scenario += c1.getCirculatingSupply(target=alice).run(sender=alice)
        
        scenario.h3("Admin2 mint 1000 tokens to Bob")
        scenario += c1.mint(toAddr=bob, amount=1000 * factor).run(sender=admin2)
        
        scenario.h3("Admin2 mint 1234.5678 tokens to Alice")
        scenario += c1.mint(toAddr=alice, amount=1234567800).run(sender=admin2)
        
        scenario.h3("Admin2 mint 200 tokens to Jack (address is locked)")
        scenario += c1.mint(toAddr=jack, amount=200 * factor).run(sender=admin2)
        
        scenario.h3("Get balance of Bob to verify tokens have been minted")
        scenario += c1.getBalance(owner=bob, target=bob).run(sender=bob)
        
        scenario.h3("Get balance of Alice to verify tokens have been minted")
        scenario += c1.getBalance(owner=alice, target=alice).run(sender=alice)
        
        scenario.h3("Get balance of Jack to verify tokens have not been minted")
        scenario += c1.getBalance(owner=jack, target=jack).run(sender=jack)
        
        scenario.h3("Get circulating supply to verify it has been updated")
        scenario += c1.getCirculatingSupply(target=alice).run(sender=alice)
        
        scenario.h3("Get supply limit to verify it has been updated")
        scenario += c1.getSupplyLimit(target=alice).run(sender=alice)
        
        scenario.h3("Admin2 mint 199M tokens to Alice")
        scenario += c1.mint(toAddr=alice, amount=200000000 * factor).run(sender=admin2, valid=False)
        
        scenario.h3("Get circulating supply to verify it has not been updated")
        scenario += c1.getCirculatingSupply(target=alice).run(sender=alice)
        
        
        #############################
        scenario.h2("Test dispatch royalties feature")
        scenario.h3("Jack tries to send royalties to CVR holders")
        scenario += c1.dispatchRoyalties(addresses=[jack], amount= 100000000).run(sender=jack, amount=sp.tez(100), valid=False)
        
        # test not available on smartpy
        # scenario.h3("Admin2 tries to send royalties to CVR holders but do not have enough XTZ")
        # scenario += c1.dispatchRoyalties(addresses=[alice, bob]).run(sender=admin2, amount=sp.tez(100), valid=False)
        
        scenario.h3("Admin2 sends 100 XTZ royalties to alice, bob and jack")
        scenario += c1.dispatchRoyalties(addresses=[alice, bob, jack], amount= 100000000).run(sender=admin2, amount=sp.tez(100))
        
        scenario.h3("Admin2 sends 12345.6789 XTZ royalties to Alice and Bob")
        scenario += c1.dispatchRoyalties(addresses=[alice, bob], amount=12345678900).run(sender=admin2, amount=sp.mutez(12345678900))
        
        scenario.h3("Admin2 sends the rest of the 12345.6789 XTZ royalties to Jack")
        scenario += c1.dispatchRoyalties(addresses=[jack], amount=12345678900).run(sender=admin2)
        
        
        #############################
        scenario.h2("Test features with non existing address in Big Map balances")
        scenario.h3("Admin2 locks johndoe1's address")
        scenario += c1.lockAddress(address=johndoe1).run(sender=admin2, valid=False)
        
        scenario.h3("Admin2 unlocks johndoe2's address")
        scenario += c1.unlockAddress(address=johndoe2).run(sender=admin2, valid=False)
        
        scenario.h3("Get balance of Johndoe3")
        scenario += c1.getBalance(owner=johndoe3, target=johndoe3).run(sender=johndoe3)
        
        scenario.h3("Johndoe4 burns 10 tokens owned by Johndoe4")
        scenario += c1.burn(fromAddr=johndoe4, amount=10 * factor).run(sender=johndoe4, valid=False)
        
        scenario.h3("Admin2 resume sale = set sale status to True")
        scenario += c1.resumeSale().run(sender=admin2)
        
        scenario.h3("Johndoe5 buys 1000 tokens with 1000 tez")
        scenario += c1.sale().run(sender=johndoe5, amount=sp.tez(100))
        
        scenario.h3("Admin2 mint 100 tokens to Johndoe6")
        scenario += c1.mint(toAddr=johndoe6, amount=100 * factor).run(sender=admin2)
        
        scenario.h3("Admin2 aidrop 200 tokens to a list of one wallet: Johndoe7")
        scenario += c1.cvrDrop(addresses=[johndoe7], amount=200 * factor).run(sender=admin2)
        
        scenario.h3("Admin2 sends 100 XTZ royalties to Johndoe8")
        scenario += c1.dispatchRoyalties(addresses=[johndoe8], amount= 100000000).run(sender=admin2, amount=sp.tez(100))
        
        scenario.h3("Admin2 unlock transfer function, set transfer status to True")
        scenario += c1.resumeTransfer().run(sender=admin2)
        
        scenario.h3("Johndoe9 transfers 10 token from Johndoe9 to Johndoe10")
        scenario += c1.transfer(fromAddr=johndoe9, toAddr=johndoe10, amount=10 * factor).run(sender=johndoe9, valid=False)
        
        scenario.h3("Manager2 sales 1000 CVR to Johndoe11")
        scenario += c1.offchainSale(address=johndoe11, amount=1000000000).run(sender=manager2)
