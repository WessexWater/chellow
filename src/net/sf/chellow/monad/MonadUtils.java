/*
 
 Copyright 2005 Meniscus Systems Ltd
 
 This file is part of Chellow.

 Chellow is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 Chellow is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Chellow; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 */

package net.sf.chellow.monad;

import java.io.File;
import java.io.PrintWriter;
import java.io.StringWriter;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MonadUtils {
	private static Document getEmptyDocument() throws InternalException {
		DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
		DocumentBuilder db;

		try {
			db = dbf.newDocumentBuilder();
		} catch (ParserConfigurationException e) {
			throw new InternalException("Problem with Parser Configuration: "
					+ e.getMessage());
		}
		return db.newDocument();
	}

	public static Document newSourceDocument() throws InternalException {
		Document doc = getEmptyDocument();
		Element source = doc.createElement("source");

		doc.appendChild(source);
		return doc;
	}

	public static Element toXML(Document doc, VFParameter parameter) {
		Element parameterElement = doc.createElement("Parameter");

		parameterElement.setAttribute("name", parameter.getName());
		parameterElement.setAttribute("value", parameter.getValue());
		return parameterElement;
	}

	public static File checkDirectory(File directory) throws HttpException {
		if (!directory.exists()) {
			throw new DeployerException("The file '" + directory
					+ "' does not exist.");
		}
		if (directory.isFile()) {
			throw new DeployerException("The file '" + directory
					+ "' is not a directory.");
		}
		if (!directory.canRead()) {
			throw new DeployerException("The directory '" + directory
					+ "' is not readable.");
		}
		return directory;
	}

	public static File checkFile(File file) throws HttpException {
		if (!file.exists()) {
			throw new DeployerException("The file '" + file
					+ "' does not exist.");
		}
		if (!file.isFile()) {
			throw new DeployerException("The file '" + file
					+ "' is not a true file.");
		}
		if (!file.canRead()) {
			throw new DeployerException("The file '" + file
					+ "' is not readable.");
		}
		return file;
	}

	public static String getStackTrace(Throwable e) {
		StringWriter writer = new StringWriter();
		PrintWriter printWriter = new PrintWriter(writer);
		Throwable cause = ((InternalException) e).getCause();
		e.printStackTrace(printWriter);
		if (cause != null) {
			printWriter.write("\n------------\nNested exception:\n");
			cause.printStackTrace(printWriter);
		}
		return writer.toString();
	}
}