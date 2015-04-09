package edu.unr.nccp;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.sis.internal.jaxb.gmi.MI_Metadata;

import java.io.File;
import java.io.IOException;
import java.net.URISyntaxException;
import java.util.Date;
import java.util.Properties;

/**
 * Author: Moinul Hossain
 * date: 9/26/2014
 */
public class XMLMetadataGenerator {
  private static final Logger LOGGER = LogManager.getLogger("XMLMetadataGenerator");
  public static void main(String[] args) {

    String inputDir = "data-metadata";
    String outputDir = "data-metadata-output";

    if(args.length!=2){
      LOGGER.error("Please provide input and output directory");
      return;
    }

    inputDir = args[0];
    outputDir = args[1];


    /*Load the static tet values */
    Properties props = XMLMetadataGeneratorUtils.readDefaultProperties();
    Properties overriddenProps = XMLMetadataGeneratorUtils.readProperties("defaults.properties");
    props.putAll(overriddenProps);

    /* Load the metadata files */
    File[] metadataFiles = XMLMetadataGeneratorUtils.getMetadataFiles(inputDir, "metadata");
    File output = new File(outputDir);

    if(!output.exists()){
      output.mkdirs();
    }

    try {
      for (File metadataFile: metadataFiles){
        LOGGER.info("Creating metadata file for "+metadataFile.getAbsolutePath());
        String dateAndSensorId[] =  metadataFile.getName().split("-");
        //String date = dateAndSensorId[0] + dateAndSensorId[1] + "-01";
        //String sensorId = dateAndSensorId[2];
        //Properties properties = new Properties(props);
        //properties.put("date",date);
        //properties.put();
        MI_Metadata metadata = XMLMetadataGeneratorUtils.generateDefaultMI_Metadata(props,XMLMetadataGeneratorUtils.readFileContent(metadataFile));
        String outputFileName = outputDir+"/"+metadataFile.getName()+".xml";
        XMLMetadataGeneratorUtils.marshalXml(metadata,outputFileName);
      }
    }catch (URISyntaxException e){
      LOGGER.error(e);
    }
    catch (IOException ioEx){
      LOGGER.error(ioEx);
    }
   /* Properties properties = XMLMetadataGeneratorUtils.readDefaultProperties();
    LOGGER.info(properties);
    try {
      MI_Metadata metadata = XMLMetadataGeneratorUtils.generateDefaultMI_Metadata(properties,XMLMetadataGeneratorUtils.readFileContent(metadataFiles[0]));
      XMLMetadataGeneratorUtils.marshalXml(metadata,"data.xml");
    } catch (URISyntaxException e) {
      LOGGER.error(e);
    }
    catch (IOException iE){
      LOGGER.error(iE);
    }*/



  }
}
