// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title AgroIAToken
 * @dev Contrato ERC-20 para el ecosistema Agente-IA-Agro-Inteligente.
 * Soporta minteo para recompensas DePIN y quema para casos de uso deflacionarios.
 */
contract AgroIAToken is ERC20, ERC20Burnable, Ownable {
    constructor(address initialOwner)
        ERC20("Agro IA Token", "AGRO")
        Ownable(initialOwner)
    {
        // Emisión inicial de 100,000,000 de tokens al creador del contrato
        _mint(initialOwner, 100000000 * 10 ** decimals());
    }

    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}