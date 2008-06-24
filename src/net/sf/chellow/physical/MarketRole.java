package net.sf.chellow.physical;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
import java.util.List;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import com.Ostermiller.util.CSVParser;

public class MarketRole extends PersistentEntity {
	static public MarketRole getMarketRole(Long id) throws HttpException {
		MarketRole marketRole = (MarketRole) Hiber.session().get(MarketRole.class, id);
		if (marketRole == null) {
			throw new NotFoundException();
		}
		return marketRole;
	}
	
	static public void loadFromCsv() throws InternalException, UserException {
		try {
			ClassLoader classLoader = Participant.class.getClassLoader();
			CSVParser parser = new CSVParser(new InputStreamReader(classLoader
					.getResource(
							"net/sf/chellow/physical/MarketRole.csv")
					.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();
			if (titles.length < 2
					|| !titles[0].trim().equals("Market Participant Role Code")
					|| !titles[1].trim().equals("Market Role Description")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "'Market Participant Role Code, Market Role Description'.");
			}
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				insertMarketRole(values[0], values[1]);
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	static private MarketRole insertMarketRole(String code, String description) {
		MarketRole role = new MarketRole(code, description);
		Hiber.session().save(role);
		Hiber.flush();
		return role;
	}
	
	private String code;
	private String description;

	public MarketRole() {

	}

	public MarketRole(String code, String description) {
		this.code = code;
		this.description = description;
	}

	public String getCode() {
		return code;
	}

	public void setCode(String code) {
		this.code = code;
	}

	public String getDescription() {
		return description;
	}

	public void setDescription(String description) {
		this.description = description;
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
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws HttpException {
		setTypeName("market-role");
		Element element = (Element) super.toXml(doc);

		element.setAttribute("code", code);
		element.setAttribute("description", description);
		return element;
	}
}