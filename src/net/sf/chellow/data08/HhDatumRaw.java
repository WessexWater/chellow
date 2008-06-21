package net.sf.chellow.data08;

import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.types.MonadObject;
import net.sf.chellow.physical.HhDatumStatus;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.IsImport;
import net.sf.chellow.physical.IsKwh;

public class HhDatumRaw extends MonadObject {
	private MpanCoreRaw core;

	private IsImport isImport;

	private IsKwh isKwh;

	private HhEndDate endDate;

	private float value;

	private Character status;

	public HhDatumRaw(MpanCoreRaw core, IsImport isImport, IsKwh isKwh,
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

	public IsImport getIsImport() {
		return isImport;
	}

	public IsKwh getIsKwh() {
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
