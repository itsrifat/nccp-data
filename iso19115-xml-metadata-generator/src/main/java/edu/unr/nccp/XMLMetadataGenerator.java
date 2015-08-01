package edu.unr.nccp;

import com.beust.jcommander.JCommander;
import org.apache.commons.lang.StringUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.sis.internal.jaxb.gmi.MI_Metadata;

import java.io.File;
import java.net.URISyntaxException;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Properties;

import org.apache.commons.io.FilenameUtils;

/**
 * Author: Moinul Hossain
 * date: 9/26/2014
 */
public class XMLMetadataGenerator {
  private static final Logger LOGGER = LogManager.getLogger("XMLMetadataGenerator");

  public static void theMain(String args[]){
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

    //create the output dir
    File output = new File(outputDir);
    if(!output.exists()){
      output.mkdirs();
    }


    try {
      for (File metadataFile: metadataFiles){
        //LOGGER.info(metadataFiles.length);
        LOGGER.info("Creating metadata file for "+metadataFile.getAbsolutePath());
        //String dateAndSensorId[] =  metadataFile.getName().split("-");
        //System.out.println(metadataFil);
        Map<String,String> metadataValues = XMLMetadataGeneratorUtils.readFileMetadata(metadataFile,numLines);
        //LOGGER.info("metadata size: "+metadataValues.size());
        MI_Metadata metadata = XMLMetadataGeneratorUtils.generateDefaultMI_Metadata(props,
                XMLMetadataGeneratorUtils.makeTitle(metadataFile,numLines),
                XMLMetadataGeneratorUtils.makeAbstract(metadataFile, numLines),metadataValues);
        String outputFileName = outputDir+"/"+FilenameUtils.removeExtension(metadataFile.getName())+".xml";
        XMLMetadataGeneratorUtils.marshalXml(metadata,outputFileName);
      }
    }catch (URISyntaxException e){
      LOGGER.error(e);
    }
    catch (Exception ex){
      LOGGER.error(ex);
    }
    LOGGER.info("NUmber of file processed: "+metadataFiles.length);
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

  public static void main(String[] args) {
    //testFiles();
    theMain(args);
    //testValidation();
    //System.out.println(XMLMetadataGeneratorUtils.makeTitle(new File("")));
    //testTitle();
    //String theArgs = "-indir sensor.nevada.edu -infileext csv -outdir testmeta -lines 10";
    //theMain(theArgs.split(" "));

  }

  public static void testValidation(){
    //MI_Metadata metadata = XMLMetadataGeneratorUtils.generateDefaultMI_Metadata(props,XMLMetadataGeneratorUtils.readFileContent(metadataFile,numLines));
    //Validators.validate(metadata);

  }
  public static void testFiles(){
    List<File> files = XMLMetadataGeneratorUtils.listFileTree(new File("/home/mdmoinulh/nrdc_dataone/sensor.nevada.edu/"));
    for (File metadataFile: files) {
      if (metadataFile.getName().endsWith("csv"))
        LOGGER.info(metadataFile.getAbsolutePath());
    }

  }

  public static void testTitle(){
    System.out.println(XMLMetadataGeneratorUtils.makeTitle(new File("/home/mdmoinulh/Downloads/NRDC-NCCP-Rockland_Met_OneMin_2013_11_8370_49842.csv"),10));
    System.out.println(XMLMetadataGeneratorUtils.makeAbstract(new File("/home/mdmoinulh/Downloads/NRDC-NCCP-Rockland_Met_OneMin_2013_11_8370_49842.csv"),10));
  }


}
