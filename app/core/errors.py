# app/core/errors.py
import re

def get_friendly_db_error(e: Exception) -> str:
    """
    Converte exceções do SQLAlchemy/banco de dados em mensagens amigáveis
    para o usuário, especialmente em caso de duplicidade de registros.
    """
    err_msg = str(e)
    
    # Verifica por violações de chave única / duplicidade
    # SQLite: UNIQUE constraint failed: table.column
    # PostgreSQL: duplicate key value violates unique constraint "constraint_name"
    # Detail: Key (column)=(value) already exists.
    err_lower = err_msg.lower()
    
    if any(k in err_lower for k in ["unique constraint", "duplicate key", "unique constraint failed", "constraint failed", "duplicate"]):
        if "e_patrimonio" in err_lower or "patrimonio" in err_lower:
            return "Já existe um ativo cadastrado com este número de Patrimônio."
        if "numero_serie" in err_lower or "serial" in err_lower:
            return "Já existe um ativo cadastrado com este Número de Série."
        if "email" in err_lower:
            return "Já existe um usuário cadastrado com este endereço de E-mail."
        if "matricula" in err_lower:
            return "Já existe um usuário cadastrado com esta Matrícula."
        if "cnpj" in err_lower:
            return "Já existe um fornecedor cadastrado com este CNPJ."
        if "numero_nota" in err_lower or "nota_fiscal" in err_lower:
            return "Já existe uma nota fiscal cadastrada com este número."
        if "nome" in err_lower:
            return "Já existe um registro com este Nome cadastrado."
            
        return "Este registro já existe no sistema (campo duplicado)."
        
    # Verifica por violação de integridade referencial (chave estrangeira)
    if any(k in err_lower for k in ["foreign key constraint", "violates foreign key", "key is still referenced"]):
        return "Não é possível realizar esta ação pois este registro está sendo usado por outro módulo do sistema."

    return err_msg
