/*
 
 Copyright 2008 Meniscus Systems Ltd
 
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

package net.sf.chellow.physical;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.CSVParser;

public class MeasurementRequirement extends PersistentEntity {
	static public MeasurementRequirement getMeasurementRequirement(Long id) throws HttpException {
		MeasurementRequirement requirement = (MeasurementRequirement) Hiber.session().get(MeasurementRequirement.class, id);
		if (requirement == null) {
			throw new UserException(
					"There is no measurement requirement with that id.");
		}
		return requirement;
	}

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = MeasurementRequirement.class.getClassLoader();
			CSVParser parser = new CSVParser(new InputStreamReader(classLoader
					.getResource(
							"net/sf/chellow/physical/MeasurementRequirement.csv")
					.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();

			if (titles.length < 11
					|| !titles[0].trim().equals("Standard Settlement Configuration Id")
					|| !titles[1].trim().equals(
							"Time Pattern Regime Id")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "Standard Settlement Configuration Id, Time Pattern Regime Id.");
			}
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				Ssc ssc = Ssc.getSsc(values[0]);
				ssc.insertMeasurementRequirement(Tpr.getTpr(values[1]));
				}			
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	private Ssc ssc;

	private Tpr tpr;

	public MeasurementRequirement() {
	}

	public MeasurementRequirement(Ssc ssc, Tpr tpr) throws HttpException {
		setSsc(ssc);
		setTpr(tpr);
	}

	void setSsc(Ssc ssc) {
		this.ssc = ssc;
	}

	public Ssc getSsc() {
		return ssc;
	}

	public Tpr getTpr() {
		return tpr;
	}

	void setTpr(Tpr tpr) {
		this.tpr = tpr;
	}

	public Node toXml(Document doc) throws HttpException {
		setTypeName("measurement-requirement");

		Element element = (Element) super.toXml(doc);
		return element;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc, new XmlTree("dso")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}
	/*
	 * public void insertRegister(Ssc.Units units, String tprString) throws
	 * ProgrammerException, UserException { Set<Tpr> tprs = new HashSet<Tpr>();
	 * for (String tprCode : tprString.split(",")) { Tpr tpr =
	 * Tpr.getTpr(tprCode); tprs.add(tpr); } registers.add(new Ssc(this, units,
	 * tprs)); }
	 */
}