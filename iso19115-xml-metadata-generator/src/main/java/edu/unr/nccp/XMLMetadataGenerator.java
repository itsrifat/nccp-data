package edu.unr.nccp;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.sis.internal.jaxb.gmi.MI_Metadata;

import java.io.File;
import java.net.URISyntaxException;
import java.util.Properties;

/**
 * Author: Moinul Hossain
 * date: 9/26/2014
 */
public class XMLMetadataGenerator {
  private static final Logger LOGGER = LogManager.getLogger("XMLMetadataGenerator");
  public static void main(String[] args) {

    /*Load the static tet values */
    Properties props = XMLMetadataGeneratorUtils.readDefaultProperties();
    Properties overriddenProps = XMLMetadataGeneratorUtils.readProperties("defaults.properties");
    props.putAll(overriddenProps);

    /* Load the metadata files */
    File[] metadataFiles = XMLMetadataGeneratorUtils.getMetadataFiles("data-metadata", "metadata");

    try {
      for (File f: metadataFiles){
        MI_Metadata metadata = XMLMetadataGeneratorUtils.generateDefaultMI_Metadata(props);
        XMLMetadataGeneratorUtils.marshalXml(metadata,"data-metadata-output"+File.pathSeparator+f.getName()+".xml");
      }
    }catch (URISyntaxException e){
      LOGGER.error(e);
    }

/*
    Properties properties = XMLMetadataGeneratorUtils.readDefaultProperties();
    LOGGER.info(properties);
    try {
      MI_Metadata metadata = XMLMetadataGeneratorUtils.generateDefaultMI_Metadata(properties);
      XMLMetadataGeneratorUtils.marshalXml(metadata,"data.xml");
    } catch (URISyntaxException e) {
      LOGGER.error(e);
    }
*/



  }
}
