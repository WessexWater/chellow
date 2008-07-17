package net.sf.chellow.data08;

import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.types.MonadObject;
import net.sf.chellow.physical.HhDatumStatus;
import net.sf.chellow.physical.HhEndDate;

public class HhDatumRaw extends MonadObject {
	private MpanCoreRaw core;

	private boolean isImport;

	private boolean isKwh;

	private HhEndDate endDate;

	private float value;

	private Character status;

	public HhDatumRaw(MpanCoreRaw core, boolean isImport, boolean isKwh,
			HhEndDate endDate, float value, HhDatumStatus status)
			throws InternalException {
		this.core = core;
		this.isImport = isImport;
		this.isKwh = isKwh;
		if (endDate == null) {
			throw new InternalException(
					"The value 'endDate' must not be null.");
		}
		this.endDate = endDate;
		this.value = value;
		if (status == null) {
			this.status = null;
		} else {
			this.status = status.getCharacter();
		}
	}

	public MpanCoreRaw getMpanCore() {
		return core;
	}

	public boolean getIsImport() {
		return isImport;
	}

	public boolean getIsKwh() {
		return isKwh;
	}

	public HhEndDate getEndDate() {
		return endDate;
	}

	public float getValue() {
		return value;
	}

	public Character getStatus() {
		return status;
	}

	public String toString() {
		return "MPAN core: " + core + ", Is import? " + isImport + ", Is Kwh? "
				+ isKwh + ", End date " + endDate + ", Value " + value
				+ ", Status " + status;
	}
}
