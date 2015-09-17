package edu.unr.nccp;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.sis.internal.geoapi.temporal.Instant;
import org.apache.sis.internal.geoapi.temporal.Period;
import org.apache.sis.internal.geoapi.temporal.Position;
import org.apache.sis.internal.jaxb.gmi.MI_Metadata;
import org.apache.sis.internal.util.CheckedArrayList;
import org.apache.sis.metadata.iso.citation.*;
import org.apache.sis.metadata.iso.extent.DefaultExtent;
import org.apache.sis.metadata.iso.extent.DefaultTemporalExtent;
import org.apache.sis.metadata.iso.identification.DefaultDataIdentification;
import org.apache.sis.metadata.iso.identification.DefaultKeywords;
import org.apache.sis.util.collection.CodeListSet;
import org.apache.sis.util.iso.DefaultInternationalString;
import org.apache.sis.util.iso.SimpleInternationalString;
import org.opengis.metadata.citation.DateType;
import org.opengis.metadata.citation.Role;
import org.opengis.metadata.identification.CharacterSet;
import org.opengis.metadata.maintenance.ScopeCode;
import org.opengis.util.InternationalString;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBException;
import javax.xml.bind.Marshaller;
import java.io.*;
import java.net.URI;
import java.net.URISyntaxException;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;

/**
 * Author: Moinul Hossain
 * date: 9/26/2014
 */
public class XMLMetadataGeneratorUtils {
  private static final Logger LOGGER = LogManager.getLogger("XMLMetadataGeneratorUtils");

  public static final String DATA_METEOROLOGICAL="Met";
  public static final String DATA_VEGETATION="Veg";
  public static final String DATA_METEOROLOGICAL_DESC="meteorological";
  public static final String DATA_VEGETATION_DESC="megetation";
  public static final String DATA_INTERVAL_ONE_MINUTE = "OneMin";
  public static final String DATA_INTERVAL_TEN_MINUTE = "TenMin";


  public static Properties readDefaultProperties(){
    Properties props = new Properties();
    InputStream input;
    String filename = "/edu/unr/nccp/defaults.properties";
    try {
      LOGGER.info("Loading Default Values for xml file.");
      input = XMLMetadataGeneratorUtils.class.getResourceAsStream(filename);
      if (input == null) {
        LOGGER.error("Sorry, unable to find the default properties file: " + filename);
        return null;
      }
      props.load(input);
    } catch (IOException e) {
      LOGGER.error(e);
    }
    return props;

  }
  public static Properties readProperties(String filePath){
    Properties props = new Properties();
    InputStream in;
    try {
      LOGGER.info("Loading Overridden Values for xml file.");
      in = new FileInputStream(new File(filePath));
      props.load(in);

    } catch (IOException e) {
      LOGGER.warn("You haven't specified a defaults.properties file. " +
          "Please create a defaults.properties in the same directory of the jar");
    }

    return props;

  }

  /**
   * This function builds up a metadata file with the given default values as a key-value properties object
   * @param props
   * @return
   * @throws URISyntaxException
   */
  public static MI_Metadata generateDefaultMI_Metadata(Properties props,String title, String abstractStr,
                                                       final Map<String,String> metadataValues) throws URISyntaxException {
    MI_Metadata metadata = new MI_Metadata();
    metadata.setLanguage(Locale.ENGLISH);
    metadata.setCharacterSet(CharacterSet.UTF_8);
    List scopeCodes = new ArrayList<CodeListSet>();
    scopeCodes.add(ScopeCode.DATASET);
    metadata.setHierarchyLevels(scopeCodes);

    DefaultResponsibleParty responsibleParty = new DefaultResponsibleParty();

    DefaultContact contactInfo = new DefaultContact();
    DefaultTelephone telephone = new DefaultTelephone();
    CheckedArrayList voices = new CheckedArrayList(String.class);
    voices.add(props.getProperty("telephone"));
    telephone.setVoices(voices);

    DefaultAddress address = new DefaultAddress();
    address.setAdministrativeArea(new SimpleInternationalString(props.getProperty("state")));
    address.setCity(new SimpleInternationalString(props.getProperty("city")));
    address.setCountry(new SimpleInternationalString(props.getProperty("country")));
    address.setPostalCode(new String(props.getProperty("postalCode")));
    List deliveryPoints = new CheckedArrayList(String.class);
    deliveryPoints.add(props.getProperty("addressLine1"));
    deliveryPoints.add(props.getProperty("addressLine2"));
    address.setDeliveryPoints(deliveryPoints);
    List emails = new CheckedArrayList(String.class);
    emails.add(props.getProperty("email"));
    address.setElectronicMailAddresses(emails);

    DefaultOnlineResource onlineResource = new DefaultOnlineResource();
    onlineResource.setLinkage(new URI(props.getProperty("linkageURI")));
    onlineResource.setName(props.getProperty("name"));

    contactInfo.setPhone(telephone);
    contactInfo.setAddress(address);
    contactInfo.setOnlineResource(onlineResource);

    Role role = Role.CUSTODIAN;

    responsibleParty.setOrganisationName(new SimpleInternationalString(props.getProperty("organisationName")));
    responsibleParty.setContactInfo(contactInfo);
    responsibleParty.setRole(role);


    List contacts = new CheckedArrayList(DefaultResponsibleParty.class);

    contacts.add(responsibleParty);
    metadata.setContacts(contacts);

    metadata.setDateStamp(new Date());
    metadata.setMetadataStandardName(props.getProperty("metadataStandardName"));
    metadata.setMetadataStandardVersion(props.getProperty("metadataStandardVersion"));
    metadata.setDataSetUri(props.getProperty("datasetURI"));

    List identificationInfo = new CheckedArrayList(DefaultDataIdentification.class);

    DefaultDataIdentification identification = new DefaultDataIdentification();

    List langs = new CheckedArrayList(Locale.class);
    langs.add(Locale.ENGLISH);
    identification.setLanguages(langs);

    DefaultCitation citation = new DefaultCitation();
    //citation.setTitle(new SimpleInternationalString(props.getProperty("citationTitle")));
    citation.setTitle(new SimpleInternationalString(title));
    List dates = new CheckedArrayList(DefaultCitationDate.class);
    DefaultCitationDate citationDate = new DefaultCitationDate();
    citationDate.setDate(new Date());
    DateType dateType= DateType.PUBLICATION;
    citationDate.setDateType(dateType);
    dates.add(citationDate);
    citation.setDates(dates);
    //citation.setEditionDate(new Date());


/*
    List extents = new CheckedArrayList(DefaultExtent.class);
    DefaultExtent extent = new DefaultExtent();

    final SimpleDateFormat dateFormat = new SimpleDateFormat("M/d/yyyy HH:mm:ss a");
    List temporalElements = new CheckedArrayList(DefaultTemporalExtent.class);
    DefaultTemporalExtent temporalExtent = new DefaultTemporalExtent();
    temporalExtent.setExtent(new Period() {
      public Instant getBeginning() {
        return new Instant() {
          public Position getPosition() {
            return new Position() {
              public Date getDate() {
                Date d=null;
                try {
                  d =  dateFormat.parse(metadataValues.get("Start Time"));
                } catch (ParseException e) {
                  e.printStackTrace();
                }
                return d;
              }
            };
          }
        };
      }

      public Instant getEnding() {
        return new Instant() {
          public Position getPosition() {
            return new Position() {
              public Date getDate() {
                Date d=null;
                try {
                  d =  dateFormat.parse(metadataValues.get("End Time"));
                } catch (ParseException e) {
                  e.printStackTrace();
                }
                return d;
              }
            };
          }
        };
      }
    });
    //startTemporalExtent.setBounds(new Date(), new Date());
    temporalElements.add(temporalExtent);
    extent.setTemporalElements(temporalElements);
    extents.add(extent);
*/

    //set the keywords
    List keyWordsList = new CheckedArrayList(DefaultKeywords.class);
    DefaultKeywords keywords = new DefaultKeywords();
    List keyWordsStr = new CheckedArrayList(InternationalString.class);
    String[] defaultKeyWords = props.getProperty("defaultKeyWords").split(",");
    for(String s:defaultKeyWords){
      keyWordsStr.add(new DefaultInternationalString(s));
    }

    String datatypekeyword = metadataValues.get("Logger System").equals(DATA_METEOROLOGICAL)?DATA_METEOROLOGICAL_DESC:DATA_VEGETATION_DESC;
    keyWordsStr.add(new DefaultInternationalString(datatypekeyword));

    keywords.setKeywords(keyWordsStr);
    keyWordsList.add(keywords);



    identification.setCitation(citation);
    identification.setAbstract(new SimpleInternationalString(abstractStr));
    identification.setExtents(extents);
    identification.setDescriptiveKeywords(keyWordsList);

    identificationInfo.add(identification);

    metadata.setIdentificationInfo(identificationInfo);



    return metadata;

  }

  /**
   * This function marshals an MI_Metadata object to an xml file in specified filePath
   * @param metadata
   * @param filePath
   */
  public static void marshalXml(MI_Metadata metadata,String filePath){

    try {

      File file = new File(filePath);
      JAXBContext jaxbContext = JAXBContext.newInstance(MI_Metadata.class);
      Marshaller jaxbMarshaller = jaxbContext.createMarshaller();

      // output pretty printed
      jaxbMarshaller.setProperty(Marshaller.JAXB_FORMATTED_OUTPUT, true);

      jaxbMarshaller.marshal(metadata, file);

    } catch (JAXBException e) {
      LOGGER.error(e);
    }

  }

  /**
   *
   * @param directoryPath
   * @param fileExtension
   * @return list of files form the directoryPath that has extension fileExtension
   */
  public static File[] getMetadataFiles(String directoryPath, final String fileExtension){
    List<File> files = XMLMetadataGeneratorUtils.listFileTree(new File(directoryPath));
    List<File> filesWithExtension = new ArrayList<File>();
    try{

      //files.toArray(fileArray); // fill the array
      int i=0;
      for (File metadataFile: files) {
        if (metadataFile.getName().endsWith(fileExtension)){
          filesWithExtension.add(metadataFile);
        }
      }

    }catch (Exception e){
      LOGGER.error(e);
    }


    return filesWithExtension.toArray(new File[filesWithExtension.size()]);
  }
  public static String readFileContent(File f) throws IOException{
    BufferedReader br = new BufferedReader(new FileReader(f));
    StringBuilder sb= new StringBuilder();
    try {

      String line = br.readLine();

      while (line != null) {
        sb.append(line);
        sb.append("\n");
        line = br.readLine();
      }
    } catch(IOException e){
      LOGGER.error(e);
    }
    finally {
      br.close();
    }

    return sb.toString();
  }


  /*
  * This method extracts first n lines from a file.
  * Its used to extract the meta information from the csv files and put them in abstract of metadata files
  *
  * */
  public static String readFileContent(File f,int numLines) throws IOException{
    BufferedReader br = new BufferedReader(new FileReader(f));
    StringBuilder sb= new StringBuilder();
    try {

      String line = br.readLine();
      int i=0;
      while (i<numLines && line != null) {
        sb.append(line);
        sb.append("\n");
        line = br.readLine();
        i++;
      }
      //return sb.toString();
    } catch(IOException e){
      LOGGER.error(e);
    }
    finally {
      br.close();
    }

    return sb.toString();
  }
  public static Map readFileMetadata(File f,int numLines) throws IOException{
    Map<String,String> data = new HashMap<String, String>();
    BufferedReader br = new BufferedReader(new FileReader(f));
    //StringBuilder sb= new StringBuilder();
    try {
      //LOGGER.info("Reading file metadata content");
      String line = br.readLine();
      int i=0;
      while (i<numLines && line != null) {
        String[] datastr = line.split(":",2);
        data.put(datastr[0],datastr[1].replace(","," ").trim());
        line = br.readLine();
        i++;
      }
      //return sb.toString();
    } catch(IOException e){
      LOGGER.error(e);
    }
    finally {
      br.close();
    }

    return data;
  }
  /*
  taken from http://stackoverflow.com/questions/2056221/recursively-list-files-in-java/2056352#2056352
   */
  public static List<File> listFileTree(File dir) {
    List<File> fileTree = new ArrayList<File>();
    for (File entry : dir.listFiles()) {
      if (entry.isFile()) fileTree.add(entry);
      else fileTree.addAll(listFileTree(entry));
    }
    return fileTree;
  }

  public static String makeTitle(File f,int numLines){
    String titleHolder = "Monthly Aggregated %s Data of  %s site from date %s to date %s";
    String title="";
    try{
      Map<String,String> metadata = readFileMetadata(f,numLines);
      //String dataType = f.getAbsolutePath().contains(DATA_METEOROLOGICAL)?DATA_METEOROLOGICAL_DESC:DATA_VEGETATION_DESC;
      String dataType = metadata.get("Logger System").equals(DATA_METEOROLOGICAL)?DATA_METEOROLOGICAL_DESC:DATA_VEGETATION_DESC;

      title = String.format(titleHolder, dataType,metadata.get("Site"),metadata.get("Start Time"),metadata.get("End Time"));
    }
    catch (Exception e){

    }

    return title.trim();
  }

  public static String makeAbstract(File f,int numLines){
    String abstractHolder = "This file contains Monthly Aggregated %s Data of %s site from date %s to date %s. " +
            "The date times are according to time zone %s.";
    String theAbstract="";
    try{
      //String dataType = f.getAbsolutePath().contains(DATA_METEOROLOGICAL)?DATA_METEOROLOGICAL_DESC:DATA_VEGETATION_DESC;
      Map<String,String> metadata = readFileMetadata(f,numLines);
      String dataType = metadata.get("Logger System").equals(DATA_METEOROLOGICAL)?DATA_METEOROLOGICAL_DESC:DATA_VEGETATION_DESC;
      theAbstract = String.format(abstractHolder, dataType,metadata.get("Site"),
                          metadata.get("Start Time"),metadata.get("End Time"),metadata.get("Time Zone"));
    }
    catch (Exception e){

    }

    return theAbstract.trim();
  }

}
