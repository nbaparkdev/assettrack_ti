import sqlite3

def add_columns():
    conn = sqlite3.connect('assettrack.db')
    cursor = conn.cursor()
    columns = [
        ("data_emissao", "DATETIME"),
        ("valor_total", "FLOAT"),
        ("natureza_operacao", "VARCHAR"),
        ("emitente_nome", "VARCHAR"),
        ("emitente_cnpj", "VARCHAR"),
        ("destinatario_nome", "VARCHAR"),
        ("destinatario_cnpj", "VARCHAR")
    ]
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE notas_fiscais ADD COLUMN {col_name} {col_type}")
            print(f"Added {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns()
