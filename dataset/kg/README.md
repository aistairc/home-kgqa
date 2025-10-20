# Episodic KG

RDF resources and ontology files used by the project.

## Contents

- vh2kg_schema_v2.0.0.ttl: Ontology (vocabulary, schema) for Episodic KG.
- scene1.tar.gz (Download required): RDF files of Episodic KG. 

## Getting KG dataset

To download and set up the KG dataset:

1. Download the KG dataset:
   ```bash
   cd dataset/kg/
   wget "https://www.dropbox.com/scl/fi/om0lib4yktiigjbsv5nn5/scene1.tar.gz?rlkey=63ljrqpbiqgc09d2glwrmcgrx&st=13s0p1wu&dl=1" -O scene1.tar.gz
   ```
   Or download manually from: [scene1.tar.gz](https://www.dropbox.com/scl/fi/om0lib4yktiigjbsv5nn5/scene1.tar.gz?rlkey=63ljrqpbiqgc09d2glwrmcgrx&st=13s0p1wu&dl=0)
   
   **Note**: The download link will be replaced with Zenodo or other permanent services after paper acceptance.

2. Extract the archive:
   ```bash
   tar -zxvf scene1.tar.gz
   ```


## Loading data into GraphDB

### Installing GraphDB Free

Follow the installation instructions on the [official website](https://www.ontotext.com/products/graphdb/).

### Importing TTL files

To import all TTL files from the extracted scene1 directory into GraphDB using the preload tool:

1. **Start GraphDB** and create a repository using the Workbench
   - **Repository name**: Use `vhakg-episode-scene1` as the repository name
2. **Stop GraphDB** after creating the repository
3. **Use the preload command** to import all TTL files:
   ```bash
   # Navigate to GraphDB installation directory
   cd <graphdb-dist>/bin/
   
   # Import all TTL files from scene1 directory
   ./preload -f -i vhakg-episode-scene1 /path/to/dataset/kg/scene1/*.ttl
   ```
   
   Or for a specific repository configuration file:
   ```bash
   ./preload -c /path/to/GraphDB/data/repositories/vhakg-episode-scene1/config.ttl /path/to/dataset/kg/scene1/*.ttl
   ```

4. **Start GraphDB** after the import is complete