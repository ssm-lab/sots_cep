package schema.event;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Event {

    @JsonProperty("id")
    private String id;

    @JsonProperty("type")
    private String type;

    @JsonProperty("src")
    private String src;

    @JsonProperty("event_ts")
    private Double eventTs;

    @JsonProperty("value")
    private Double value;

    @JsonProperty("confidence")
    private Double confidence;

    @JsonProperty("event_status")
    private String eventStatus;

    @JsonProperty("value_datatype")
    private String valueDatatype;

    @JsonProperty("value_unit")
    private String valueUnit;

    @JsonProperty("extras")
    private Map<String, Object> extras;



    public Event() {}

    public Event(
            String id,
            String type,
            String src,
            String eventStatus
    ) {
        this.id = id;
        this.type = type;
        this.src = src;
        this.eventStatus = eventStatus;
    }


    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getSrc() { return src; }
    public void setSrc(String src) { this.src = src; }

    public Double getEventTs() { return eventTs; }
    public void setEventTs(Double eventTs) { this.eventTs = eventTs; }

    public Double getValue() { return value; }
    public void setValue(Double value) { this.value = value; }

    public Double getConfidence() { return confidence; }
    public void setConfidence(Double confidence) { this.confidence = confidence; }

    public String getEventStatus() { return eventStatus; }
    public void setEventStatus(String eventStatus) { this.eventStatus = eventStatus; }

    public String getValueDatatype() { return valueDatatype; }
    public void setValueDatatype(String valueDatatype) { this.valueDatatype = valueDatatype; }

    public String getValueUnit() { return valueUnit; }
    public void setValueUnit(String valueUnit) { this.valueUnit = valueUnit; }

    public Map<String, Object> getExtras() { return extras; }
    public void setExtras(Map<String, Object> extras) { this.extras = extras; }


    @Override
    public String toString() {
        return "Event{" +
                "id='" + id + '\'' +
                ", type='" + type + '\'' +
                ", src='" + src + '\'' +
                ", eventTs=" + eventTs +
                ", value=" + value +
                ", confidence=" + confidence +
                ", eventStatus='" + eventStatus + '\'' +
                ", valueDatatype='" + valueDatatype + '\'' +
                ", valueUnit='" + valueUnit + '\'' +
                ", extras=" + extras +
                '}';
    }
}
