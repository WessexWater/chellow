package net.sf.chellow.billing;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class EdiSegment {
	private List<EdiElement> elements = new ArrayList<EdiElement>();

	private String code;

	public EdiSegment(String segment, Map<Integer, Character> readTypeMap) {
		code = segment.substring(0, 3);
		for (String element : segment.substring(4).split("\\+")) {
			elements.add(new EdiElement(segment, elements.size(), element, readTypeMap));
		}
	}

	public List<EdiElement> getElements() {
		return elements;
	}

	public String getCode() {
		return code;
	}
}