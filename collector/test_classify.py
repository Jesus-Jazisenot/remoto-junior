"""Pruebas minimas de las reglas. Ejecutar: python collector/test_classify.py"""
import classify as c


def J(**k):
    base = {"fuente": "himalayas", "id": "x", "titulo": "Junior Python Developer", "empresa": "Acme", "url": "https://x",
            "descripcion": "Build things.", "seniority_fuente": [], "categorias": [], "restr_paises": [], "restr_tz": []}
    base.update(k)
    return base


def check(j, esperado):
    r, m = c.clasificar(j)
    got = "ok" if r else m
    assert got == esperado, (j["titulo"], got, esperado)


check(J(), "ok")
check(J(restr_paises=["United States"]), "ubicacion_no_latam")
check(J(restr_paises=["United States", "Mexico", "Brazil", "Chile"]), "ok")
check(J(descripcion="Candidates must be located in the US. Great team."), "exige_residencia_ciudadania")
check(J(descripcion="You must be authorized to work in the United States."), "exige_residencia_ciudadania")
check(J(titulo="Senior Python Developer"), "nivel_no_junior")
check(J(titulo="Python Developer", descripcion="Requires 3+ years of experience with Python."), "nivel_no_junior")
check(J(titulo="Python Developer", descripcion="1 year of experience with Python."), "ok")
check(J(titulo="Python Developer"), "sin_senal_de_nivel_junior")
check(J(titulo="Sales Development Representative", seniority_fuente=["Entry-level"]), "profesion_no_tecnica")
check(J(titulo="Barista", seniority_fuente=["Entry-level"]), "area_fuera_de_tecnologia")
check(J(titulo="Business Developer", seniority_fuente=["Entry-level"]), "area_fuera_de_tecnologia")
check(J(titulo="QA Tester", seniority_fuente=["Entry-level"]), "ok")
check(J(fuente="remoteok", ubicacion_txt="", descripcion="Junior role."), "ubicacion_desconocida")
check(J(fuente="remoteok", ubicacion_txt="Worldwide"), "ok")
check(J(fuente="weworkremotely", region_fuente="USA Only"), "ubicacion_no_latam")
assert c.ingles(J(descripcion="Buscamos programador con inglés avanzado"))[1] == "avanzado"
assert c.ingles(J(descripcion="Buscamos programador para equipo de la empresa con experiencia en el área"))[1] == "no_requerido"
assert c.anios_requeridos("minimum of 5 years of professional experience") == 5
check(J(titulo="Junior Data Analyst (US)"), "titulo_indica_pais_fuera_de_latam")
check(J(titulo="Data Entry Specialist", seniority_fuente=["Entry-level"]), "profesion_no_tecnica")
check(J(titulo="Junior DevOps Engineer (Remote Eligible in Bulgaria)"), "titulo_indica_pais_fuera_de_latam")
check(J(titulo="Junior Developer (Remote Eligible in Mexico)"), "ok")
print("todas las pruebas pasan")
