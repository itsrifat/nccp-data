## ISO 19115 xml metadata generator Module

This java module is used to generate iso19115 metadata for nccp monthly aggregated data fomr the plain text metadata files

To build the module: `mvn clean compile assembly:single`. It will create an executable jar called `iso19115-xml-gen.jar`.

A `defaluts.properties` file should be present in the execution directory to run the executable jar.

To run the executable jar: `java -jar iso19115-xml-gen.jar inputdirectory outputDirectory`
