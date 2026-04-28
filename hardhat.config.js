import "@nomicfoundation/hardhat-toolbox";
import * as dotenv from "dotenv";
dotenv.config();

// Solo incluir la clave privada si es un hex válido de 32 bytes (64 caracteres)
const PRIVATE_KEY = process.env.PRIVATE_KEY || "";
const isValidKey = /^(0x)?[0-9a-fA-F]{64}$/.test(PRIVATE_KEY);

/** @type import('hardhat/config').HardhatUserConfig */
export default {
    // Usamos la versión 0.8.20 para que coincida con tu contrato AgroIAToken.sol
    solidity: "0.8.20",
    networks: {
        sepolia: {
            // Cargamos la URL del nodo y la clave privada desde el archivo .env
            url: process.env.SEPOLIA_URL || "",
            accounts: isValidKey ? [PRIVATE_KEY] : [],
        },
    },
    // Configuración para verificar contratos en Etherscan
    etherscan: {
        apiKey: process.env.ETHERSCAN_API_KEY || "",
    },
};