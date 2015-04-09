package edu.unr.nccp;

import org.apache.commons.io.FilenameUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.sis.internal.jaxb.gmi.MI_Metadata;
import org.apache.sis.internal.util.CheckedArrayList;
import org.apache.sis.metadata.iso.citation.*;
import org.apache.sis.metadata.iso.identification.DefaultDataIdentification;
import org.apache.sis.util.collection.CodeListSet;
import org.apache.sis.util.iso.SimpleInternationalString;
import org.opengis.metadata.citation.DateType;
import org.opengis.metadata.citation.ResponsibleParty;
import org.opengis.metadata.citation.Role;
import org.opengis.metadata.identification.CharacterSet;
import org.opengis.metadata.maintenance.ScopeCode;

import javax.xml.bind.JAXBContext;
import javax.xml.bind.JAXBException;
import javax.xml.bind.Marshaller;
import java.io.*;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.*;

/**
 * Author: Moinul Hossain
 * date: 9/26/2014
 */
public class XMLMetadataGeneratorUtils {
  private static final Logger LOGGER = LogManager.getLogger("XMLMetadataGeneratorUtils");
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
  public static MI_Metadata generateDefaultMI_Metadata(Properties props, String mainMetadata) throws URISyntaxException {
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
    citation.setTitle(new SimpleInternationalString("NCCP Data"));

    List dates = new CheckedArrayList(DefaultCitationDate.class);
    DefaultCitationDate citationDate = new DefaultCitationDate();
    citationDate.setDate(new Date());
    DateType dateType= DateType.CREATION;
    citationDate.setDateType(dateType);
    dates.add(citationDate);
    citation.setDates(dates);
    //citation.setEditionDate(new Date());


    identification.setCitation(citation);

    identification.setAbstract(new SimpleInternationalString(mainMetadata));

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

    File dir = new File(directoryPath);

    return dir.listFiles(new FilenameFilter() {
      @Override
      public boolean accept(File dir, String name) {
        return name.toLowerCase().endsWith(fileExtension);
      }
    });

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

}
