package net.sf.chellow.monad.types;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

public class GeoPoint extends MonadObject {
	private Double latitude;

	private Double longitude;

	GeoPoint() {
		init();
	}

	public GeoPoint(Double latitude, Double longitude) {
		init();
		update(latitude, longitude);
	}

	public GeoPoint(String label, String latitudeString, String longitudeString)
			throws ProgrammerException, UserException {
		init();
		setLabel(label);
		MonadDouble latitude = new MonadDouble("latitude", latitudeString);
		MonadDouble longitude = new MonadDouble("longitude", longitudeString);

		update(latitude.getDouble(), longitude.getDouble());
	}
	
	private void update(Double latitude, Double longitude) {
		setLatitude(latitude);
		setLongitude(longitude);
	}

	private void init() {
		setTypeName("geo-point");
	}

	public Double getLatitude() {
		return latitude;
	}

	void setLatitude(Double latitude) {
		this.latitude = latitude;
	}

	public Double getLongitude() {
		return longitude;
	}

	void setLongitude(Double longitude) {
		this.longitude = longitude;
	}

	public Urlable getChild(UriPathElement arg0) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation arg0) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpPost(Invocation arg0) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation arg0) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);
		element.setAttribute("latitude", getLatitude().toString());
		element.setAttribute("longitude", getLongitude().toString());
		element.setAttribute("string", toString());
		return element;
	}

	public String toString() {
		return "GEO:" + getLatitude().toString() + ";"
				+ getLongitude().toString();
	}
}