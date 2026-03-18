## Plan de refactorización de aplicación de traducción de etiquetas

El proyecto de traducción de etiquetas tiene que escalar para ser viable incorporar nuevos idiomas y gestionar el histórico de cambios derivado de la evolución de la plataforma

Conforme se publica una nueva versión, se añaden nuevas etiquetas en el fichero, que hay que traducir a los diferentes idiomas

El sistema tiene que ser capaz de detectar en el fichero las nuevas etiquetas añadidas y traducirlas, omitiendo la traducción en las etiquetas ya traducidas.

El proyecto incorpora una base de datos de control de las traducciones con los siguientes campos: idioma-origen, idioma-destino, nombre-fichero-original, nombre-fichero-destino, fecha de traducción, total-etiquetas-traducidas y total etiquetas fichero-original

**Premisas del proyecto**

- Los ficheros traducidos se actualizan con nuevas etiquetas que hay que traducir
- Las etiquetas ya traducidas se mantienen igual
- Al fichero traducido (fichero-destino) se le modifica su nombre añadiendo la fecha de creación conforme al siguiente formato: "añomesdia-nombre del fichero original-idioma"
- Cada traducción se registra en la base de datos de control