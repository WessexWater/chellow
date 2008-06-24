package net.sf.chellow.physical;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import com.Ostermiller.util.CSVParser;

public class Participant extends PersistentEntity {
	static public Participant getParticipant(Long id) throws HttpException {
		Participant participant = (Participant) Hiber.session().get(Participant.class, id);
		if (participant == null) {
			throw new NotFoundException();
		}
		return participant;
	}
	
	static public void loadFromCsv() throws InternalException, UserException {
		try {
			ClassLoader classLoader = Participant.class.getClassLoader();
			CSVParser parser = new CSVParser(new InputStreamReader(classLoader
					.getResource(
							"net/sf/chellow/physical/MarketParticipant.csv")
					.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();
			if (titles.length < 3
					|| !titles[0].trim().equals("Market Participant Id")
					|| !titles[1].trim().equals("Market Participant Name")
					|| !titles[2].trim().equals("Pool Member Id")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "'Market Participant Id, Market Participant Name, Pool Member Id'.");
			}
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				insertParticipant(values[0], values[1]);
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	static private Participant insertParticipant(String code, String name) {
		Participant participant = new Participant(code, name);
		Hiber.session().save(participant);
		Hiber.flush();
		return participant;
	}
	
	private String code;
	private String name;

	public Participant() {

	}

	public Participant(String code, String name) {
		this.code = code;
		this.name = name;
	}

	public String getCode() {
		return code;
	}

	public void setCode(String code) {
		this.code = code;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	@Override
	public Urlable getChild(UriPathElement uriId) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public MonadUri getUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	@Override
	public void httpGet(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws HttpException {
		setTypeName("participant");
		Element element = (Element) super.toXml(doc);

		element.setAttribute("code", code);
		element.setAttribute("name", name);
		return element;
	}
}
