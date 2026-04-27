import { expect } from "chai";
import hre from "hardhat";

describe("AgroIAToken - Contrato Inteligente", function () {
    let Token, token, owner, addr1;

    // Antes de cada prueba, desplegamos el contrato en la red local de pruebas
    beforeEach(async function () {
        [owner, addr1] = await hre.ethers.getSigners();
        Token = await hre.ethers.getContractFactory("AgroIAToken");
        token = await Token.deploy(owner.address);
    });

    it("Debería asignar el suministro total (100 millones) al propietario", async function () {
        const ownerBalance = await token.balanceOf(owner.address);
        expect(await token.totalSupply()).to.equal(ownerBalance);
    });

    it("Debería permitir al propietario mintear (crear) nuevos tokens como recompensa DePIN", async function () {
        const amountToMint = hre.ethers.parseUnits("500", 18); // 500 tokens

        // El propietario mintea tokens para el agricultor (addr1)
        await token.mint(addr1.address, amountToMint);

        const addr1Balance = await token.balanceOf(addr1.address);
        expect(addr1Balance).to.equal(amountToMint);
    });

    it("Debería permitir quemar tokens (mecanismo deflacionario)", async function () {
        const initialSupply = await token.totalSupply();
        const amountToBurn = hre.ethers.parseUnits("1000", 18); // 1000 tokens

        await token.burn(amountToBurn);

        const finalSupply = await token.totalSupply();
        expect(finalSupply).to.equal(initialSupply - amountToBurn);
    });
});