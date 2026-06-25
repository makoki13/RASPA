from sqlalchemy.orm import Session
from sqlalchemy import func
from motor_geografico import procesar_ruta_gpx
from server.database import SessionLocal
from server import models

def procesar_usuario(email_usuario, nombre_usuario, ruta_gpx):
    # 1. Abrimos sesión de base de datos
    db: Session = SessionLocal()
    
    try:
        # 2. Comprobar si el usuario está registrado en la web
        usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == email_usuario).first()

        if not usuario_existente:
            print(f"❌ RECHAZADO: El correo {email_usuario} no está registrado en la web. Se ignora el GPX.")
            return 

        # Usamos el nombre de la BD
        nombre_bd = usuario_existente.nombre_publico

        # 3. Procesar la ruta
        codigos_municipios = procesar_ruta_gpx(ruta_gpx)
        if not codigos_municipios:
            print("⚠️ La ruta no contiene puntos válidos.")
            return

        # 4. Guardar municipios nuevos en la BD
        nuevos = 0
        for codigo in codigos_municipios:
            # Comprobar si ya existe para no duplicar
            ya_existe = db.query(models.MunicipioVisitado).filter(
                models.MunicipioVisitado.email_usuario == email_usuario,
                models.MunicipioVisitado.codigo_ign_municipio == codigo
            ).first()
            
            if not ya_existe:
                nuevo_registro = models.MunicipioVisitado(email_usuario=email_usuario, codigo_ign_municipio=codigo)
                db.add(nuevo_registro)
                nuevos += 1
        
        print(f"🆕 Municipios nuevos guardados para {email_usuario}: {nuevos}")

        if nuevos == 0:
            print("⚠️ Ya habías pasado por todos estos municipios. No hay puntos nuevos.")
            db.commit() # Hacemos commit para cerrar la transacción correctamente
            return

        # ---------------------------------------------------------
        # 5. SISTEMA DE PUNTUACIÓN
        # ---------------------------------------------------------
        puntos = 0
        print("\n📊 Calculando puntuación...")

        # A) 1 Punto por municipio único
        total_municipios = db.query(func.count()).filter(
            models.MunicipioVisitado.email_usuario == email_usuario
        ).scalar()
        puntos += total_municipios
        print(f"   + {total_municipios} puntos (Municipios únicos totales)")

        # B) Bonificación por completar una Provincia
        provincias = db.query(models.Provincia).all()
        
        for prov in provincias:
            total_en_prov = db.query(func.count(models.Municipio.codigo_ign)).filter(models.Municipio.id_provincia == prov.id).scalar()
            
            visitados_en_prov = db.query(func.count()).join(
                models.Municipio, models.MunicipioVisitado.codigo_ign_municipio == models.Municipio.codigo_ign
            ).filter(
                models.Municipio.id_provincia == prov.id,
                models.MunicipioVisitado.email_usuario == email_usuario
            ).scalar()

            if total_en_prov > 0 and visitados_en_prov == total_en_prov:
                puntos += total_en_prov
                print(f"   + {total_en_prov} puntos (¡PROVINCIA COMPLETADA: {prov.nombre}!)")

        # C) Bonificación por completar una Comunidad Autónoma
        ccaas = db.query(models.Ccaa).all()

        for ccaa in ccaas:
            total_en_ccaa = db.query(func.count(models.Municipio.codigo_ign)).join(
                models.Provincia, models.Municipio.id_provincia == models.Provincia.id
            ).filter(models.Provincia.id_ccaa == ccaa.id).scalar()

            visitados_en_ccaa = db.query(func.count()).join(
                models.Municipio, models.MunicipioVisitado.codigo_ign_municipio == models.Municipio.codigo_ign
            ).join(
                models.Provincia, models.Municipio.id_provincia == models.Provincia.id
            ).filter(
                models.Provincia.id_ccaa == ccaa.id,
                models.MunicipioVisitado.email_usuario == email_usuario
            ).scalar()

            if total_en_ccaa > 0 and visitados_en_ccaa == total_en_ccaa:
                puntos += total_en_ccaa
                print(f"   + {total_en_ccaa} puntos (¡¡CCAA COMPLETADA: {ccaa.nombre}!!)")

        # 6. Actualizar el total en la tabla de usuarios
        usuario_existente.puntos_totales = puntos
        db.commit()
        
        print(f"\n🏆 PUNTUACIÓN TOTAL ACTUALIZADA PARA {nombre_bd}: {puntos} puntos\n")

    except Exception as e:
        print(f"❌ Error en la base de datos: {e}")
        db.rollback() # Si falla, deshacemos los cambios
    finally:
        db.close() # Siempre cerramos la sesión