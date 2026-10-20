"""
Package clients — Stubs clients gRPC vers les services externes.

Ces clients permettent au Service Accueil de communiquer avec :
- ConsultationService (port 50052)
- LaboratoireService  (port 50053)
- RadiologieService   (port 50054)

NOTE : Ces services externes ne sont pas encore disponibles.
       Les clients sont des stubs qui gèrent les erreurs gracieusement.
       Activez via la variable d'environnement EXTERNAL_SERVICES_ENABLED=true
       une fois les services disponibles.
"""
