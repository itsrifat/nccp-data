package edu.unr.nccp;

import com.beust.jcommander.JCommander;
import org.apache.commons.lang.StringUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.sis.internal.jaxb.gmi.MI_Metadata;

import java.io.File;
import java.io.IOException;
import java.net.URISyntaxException;
import java.util.Properties;

import org.apache.commons.io.FilenameUtils;
/**
 * Author: Moinul Hossain
 * date: 9/26/2014
 */
public class XMLMetadataGenerator {
  private static final Logger LOGGER = LogManager.getLogger("XMLMetadataGenerator");
  public static void main(String[] args) {

    CommandLineParser clp = new CommandLineParser();
    JCommander jc = new JCommander(clp,args);
    if(StringUtils.isEmpty(clp.inputDir) || StringUtils.isEmpty(clp.outputDir)
        || StringUtils.isEmpty(clp.inputFileExt) || clp.lines==null){
      jc.usage();
      return;
    }
    String inputDir;
    String outputDir;
    String inFileExt = clp.inputFileExt;
    Integer numLines;

    inputDir = clp.inputDir;
    outputDir = clp.outputDir;
    numLines = clp.lines;

    LOGGER.info("Command line arguments loaded");
    LOGGER.info(inputDir+" "+outputDir+" "+numLines);
    Properties props = XMLMetadataGeneratorUtils.readDefaultProperties();
    Properties overriddenProps = XMLMetadataGeneratorUtils.readProperties("defaults.properties");
    props.putAll(overriddenProps);

    LOGGER.info("Reading input files and creating xml metadata files");
    File[] metadataFiles = XMLMetadataGeneratorUtils.getMetadataFiles(inputDir, inFileExt);
    File output = new File(outputDir);

    if(!output.exists()){
      output.mkdirs();
    }

    try {
      for (File metadataFile: metadataFiles){
        LOGGER.info("Creating metadata file for "+metadataFile.getAbsolutePath());
        //String dateAndSensorId[] =  metadataFile.getName().split("-");
        MI_Metadata metadata = XMLMetadataGeneratorUtils.generateDefaultMI_Metadata(props,XMLMetadataGeneratorUtils.readFileContent(metadataFile,numLines));
        String outputFileName = outputDir+"/"+FilenameUtils.removeExtension(metadataFile.getName())+".xml";
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
