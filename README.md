# Bella Napoli

Backend de um sistema de pedidos para uma pizzaria, desenvolvido em Python com PostgreSQL e SQLAlchemy, com foco em regras de negócio, persistência de dados, checkout, pagamentos e testes automatizados.

> **Status:** Em desenvolvimento — o núcleo de domínio e serviços do backend está implementado e validado. A camada de API HTTP será construída na próxima etapa.

## Overview

O Bella Napoli está sendo desenvolvido como um sistema de pedidos capaz de representar o fluxo de uma compra desde a configuração dos produtos até a finalização do pedido e o processamento do pagamento.

O backend atualmente contempla catálogo, variantes de produtos, clientes, endereços, pedidos, personalização de pizzas, entrega, horários de funcionamento, precificação, histórico de status e pagamentos.

A aplicação utiliza PostgreSQL para persistência, SQLAlchemy para mapeamento objeto-relacional e Alembic para versionamento do schema do banco de dados.

## Principais recursos

* Catálogo com categorias, produtos e variantes.
* Configuração de pizzas inteiras e meio a meio.
* Seleção de sabores e bordas com regras de preço.
* Cadastro de clientes e endereços.
* Pedidos com itens e dados registrados no momento da compra.
* Cálculo de subtotal, taxa de entrega e total.
* Validação de zonas de entrega atendidas.
* Controle de horários de funcionamento.
* Histórico das mudanças de status dos pedidos.
* Checkout com retirada ou entrega.
* Pagamentos em dinheiro, cartão e PIX demonstrativo.
* Controle de tentativas e estados de pagamento.
* Confirmação idempotente de pagamentos PIX.
* Expiração de pagamentos PIX.
* Migrations de banco de dados com Alembic.
* Scripts para carga inicial de catálogo, bordas, zonas de entrega e horários.
* Suíte automatizada de testes para regras de domínio e serviços.

## Arquitetura

O backend separa as responsabilidades entre regras de negócio, serviços de aplicação e persistência.

```mermaid
flowchart LR
    A[Aplicação / futura API] --> B[Services]
    B --> C[Domain]
    B --> D[SQLAlchemy Models]
    D --> E[(PostgreSQL)]

    F[Alembic] --> E
    G[Pytest] --> C
    G --> B
```

### Organização das camadas

| Diretório       | Responsabilidade                                                   |
| --------------- | ------------------------------------------------------------------ |
| `app/domain/`   | Regras de negócio, validações, precificação e transições de estado |
| `app/services/` | Fluxos de pedidos, checkout e pagamentos                           |
| `app/models/`   | Modelos SQLAlchemy persistidos no banco                            |
| `app/db/`       | Configuração da integração com o banco                             |
| `app/core/`     | Configurações centrais da aplicação                                |
| `alembic/`      | Migrations e evolução do schema                                    |
| `scripts/`      | Scripts de carga inicial e utilitários                             |
| `tests/`        | Testes automatizados                                               |

## Tech Stack

### Backend

* Python
* SQLAlchemy
* PostgreSQL
* Alembic

### Testing

* Pytest

## Estrutura do projeto

```text
bella-napoli/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── core/
│   │   ├── db/
│   │   ├── domain/
│   │   ├── models/
│   │   └── services/
│   ├── scripts/
│   ├── tests/
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
├── docs/
├── frontend/
└── README.md
```

## Banco de dados

O projeto utiliza PostgreSQL como banco de dados principal.

A evolução do schema é controlada por migrations do Alembic, atualmente cobrindo entidades relacionadas a:

* categorias e produtos;
* variantes de produtos;
* clientes e endereços;
* pedidos e itens;
* configuração de pizzas;
* bordas e preços de bordas;
* zonas de entrega;
* horários de funcionamento;
* histórico de status;
* pagamentos.

## Pagamentos PIX

O backend possui um fluxo demonstrativo de pagamento PIX com controle de estado.

Um pagamento pode seguir o fluxo:

```text
PENDING
   │
   ├── confirmação ──> PAID
   │
   └── expiração ────> EXPIRED
```

A confirmação do PIX também trata operações idempotentes, evitando processar novamente um pagamento que já esteja confirmado.

Quando um PIX expira durante o checkout, o pedido é atualizado para:

```text
PAYMENT_EXPIRED
```

permitindo uma nova tentativa de pagamento.

## Configuração

O backend utiliza variáveis de ambiente para configurar a conexão com o PostgreSQL.

A partir do diretório `backend/`, crie o arquivo `.env` usando `.env.example` como referência.

**Windows:**

```cmd
copy .env.example .env
```

**Linux / macOS:**

```bash
cp .env.example .env
```

Variáveis necessárias:

```env
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

## Testes

A suíte de testes utiliza `pytest` e cobre as principais regras de domínio e serviços do backend.

Para executar todos os testes:

```bash
python -m pytest
```

Resultado atualmente validado:

```text
150 passed
```

Os testes abrangem, entre outros:

* clientes e endereços;
* pedidos e itens;
* configuração de pizzas;
* precificação;
* entrega;
* horários de funcionamento;
* transições de status;
* checkout;
* pagamentos;
* confirmação de PIX;
* idempotência;
* expiração de PIX.

## Estado atual

**Em desenvolvimento**

O núcleo de domínio, modelos persistentes, migrations, serviços de pedidos e pagamentos e a suíte de testes já estão implementados.

A próxima etapa será a construção da camada de API HTTP sobre esses serviços, mantendo as regras de negócio separadas dos endpoints.

## Licença

Nenhuma licença open source foi definida no repositório até o momento.
