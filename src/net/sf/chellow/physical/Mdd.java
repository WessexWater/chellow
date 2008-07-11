package net.sf.chellow.physical;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.Locale;
import java.util.TimeZone;

import javax.servlet.ServletContext;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;

import com.Ostermiller.util.CSVParser;

public class Mdd {
	private CSVParser parser;
	private DateFormat dateFormat;

	public Mdd(ServletContext context, String tableName, String[] titleList)
			throws HttpException {

		try {
			parser = new CSVParser(
					new InputStreamReader(
							context
									.getResource(
											"/WEB-INF/mdd/" + tableName + ".csv")
									.openStream(), "UTF-8"));

			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();
			if (titles.length != titleList.length) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ titleList.toString());
			}
			for (int i = 0; i < titles.length; i++) {
				if (!titles[i].trim().equals(titleList[i])) {
					throw new UserException(
							"The first line of the CSV must contain the titles "
									+ titleList.toString());
				}
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
		dateFormat = new SimpleDateFormat("dd/MM/yyyy", Locale.UK);
		dateFormat.setCalendar(new GregorianCalendar(TimeZone
				.getTimeZone("GMT"), Locale.UK));
	}
	
	public String[] getLine() throws HttpException {
		try {
			return parser.getLine();
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}
	
	public Date toDate(String value) throws HttpException {
		Date date = null;
		if (value.length() != 0) {
			try {
				date = dateFormat.parse(value);
			} catch (ParseException e) {
				throw new InternalException(e);
			}
		}
		return date;
	}
}
