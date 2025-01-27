# Blockchain Application

This project is a Python-based blockchain application that provides transaction management, proof-of-work consensus, node synchronization, and a simple smart contract execution system. The project demonstrates the core concepts of blockchain technology and decentralization, emphasizing transparency and financial autonomy.

# Features

- Blockchain Core: Transaction processing, mining, and proof-of-work-based consensus.
- Decentralized Network: Node registration and consensus algorithm for maintaining an authoritative chain.
- RESTful API: Endpoints for transaction creation, mining, chain inspection, node management, and smart contract execution.

# Usage

1. Clone the repository: git clone https://github.com/yourusername/Blockchain-Simulator.git

2. Navigate to the project directory: cd Blockchain-Simulator

3. Run a server: pipenv run python blockchain.py --port <port number>

4. Interacting with the chain, mine example: curl http://127.0.0.1:<port number>/mine

5. Interacting with the chain, new transaction example:

    curl -X POST -H "Content-Type: application/json" -d '{
        "sender": "sender-address",
        "recipient": "recipient-address",
        "amount": 10
    }' http://127.0.0.1:5000/transactions/new
