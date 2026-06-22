import sqlite3

def actualizar_esquema():
    conn = sqlite3.connect('data/raspa_db.sqlite')
    cursor = conn.cursor()

    # Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            nombre_publico TEXT,
            puntos_totales INTEGER DEFAULT 0
        )
    ''')

    # Tabla de relación (Lo que ha "raspado" cada uno)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS municipios_visitados (
            email_usuario TEXT,
            codigo_ign_municipio TEXT,
            PRIMARY KEY (email_usuario, codigo_ign_municipio),
            FOREIGN KEY (email_usuario) REFERENCES usuarios(email),
            FOREIGN KEY (codigo_ign_municipio) REFERENCES municipios(codigo_ign)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Tablas de juego añadidas a la base de datos.")

if __name__ == "__main__":
    actualizar_esquema()