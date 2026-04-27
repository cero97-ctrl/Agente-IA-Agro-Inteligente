import hre from "hardhat";

async function main() {
    // Obtenemos la cuenta (signer) que realizará el despliegue
    const [deployer] = await hre.ethers.getSigners();

    console.log("Iniciando despliegue de contratos...");
    console.log("Cuenta de despliegue (Deployer):", deployer.address);

    // Obtenemos el factory del contrato AgroIAToken
    const AgroIAToken = await hre.ethers.getContractFactory("AgroIAToken");

    // Desplegamos el contrato pasando la cuenta del deployer como initialOwner
    const agroToken = await AgroIAToken.deploy(deployer.address);

    // Esperamos a que la transacción de despliegue sea minada (ethers v6)
    await agroToken.waitForDeployment();
    const contractAddress = await agroToken.getAddress();

    console.log("✅ AgroIAToken desplegado exitosamente en la dirección:", contractAddress);
}

main().catch((error) => {
    console.error("Error durante el despliegue:", error);
    process.exitCode = 1;
});