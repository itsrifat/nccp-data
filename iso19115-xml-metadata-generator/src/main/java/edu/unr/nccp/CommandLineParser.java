package edu.unr.nccp;

import com.beust.jcommander.DynamicParameter;
import com.beust.jcommander.Parameter;
import com.beust.jcommander.internal.Lists;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Author: Moinul Hossain
 * Date: 4/9/2015
 */
public class CommandLineParser {
  @Parameter(names = { "-indir" }, description = "Input files directory")
  public String inputDir;

  @Parameter(names = "-outdir", description = "Output directory for processed files")
  public String outputDir;

  @Parameter(names = "-lines", description = "Number of lines to process from each input file")
  public Integer lines ;

  @Parameter(names = { "-infileext" }, description = "Type of input files to look in indir")
  public String inputFileExt;
}
