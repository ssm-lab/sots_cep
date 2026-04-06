package patterns.esper;

import com.espertech.esper.common.client.EPCompiled;
import com.espertech.esper.common.client.configuration.Configuration;
import com.espertech.esper.compiler.client.*;
import com.espertech.esper.runtime.client.*;

import java.io.InputStreamReader;
import java.io.Reader;
import java.util.*;
import java.util.logging.Logger;

import cep.esper.EsperCEPEngine;
import schema.event.Event;
import schema.pattern.*;
import utils.PatternLogger;
import patterns.PatternManager;
import com.google.gson.*;

/**
 * Manages pattern lifecycle for Esper CEP — loading from JSON,
 * compiling and deploying patterns, and propagating confidence
 * between atomic and complex layers with hierarchical provenance tracking.
 */
public class EsperPatternManager extends PatternManager<EsperCEPEngine> {
    private static final Logger LOG = Logger.getLogger(EsperPatternManager.class.getName());

    private final PatternLogger patternLogger;
    private final EPCompiler compiler = EPCompilerProvider.getCompiler();
    private List<PatternDef> patterns;
    private final Boolean logMatches;

    public EsperPatternManager(EsperCEPEngine engine, PatternLogger logger, Boolean logMatches) {
        super(engine);
        this.patternLogger = logger;
        this.logMatches = logMatches;
    }

    // ---------------------------------------------------------------------
    // Internal helper classes for JSON loading
    // ---------------------------------------------------------------------
    private static class PatternDef {
        String name, description, epl, type;
        ConfidenceRule confidence;

        PatternDef(String n, String q, String e, String t, ConfidenceRule c) {
            name = n; description = q; epl = e; type = t; confidence = c;
        }
    }

    private static class ConfidenceRule {
        String method;
        ConfidenceRule(String m) { method = m; }
    }

    // ---------------------------------------------------------------------
    // Load pattern definitions from JSON
    // ---------------------------------------------------------------------
    @Override
    public void loadPatterns(String resource) throws Exception {
        Gson gson = new Gson();
        List<PatternDef> defs = new ArrayList<>();

        try (Reader reader = new InputStreamReader(
                getClass().getClassLoader().getResourceAsStream(resource))) {

            JsonArray arr = gson.fromJson(reader, JsonArray.class);
            for (JsonElement e : arr) {
                var o = e.getAsJsonObject();
                String name = o.get("name").getAsString();
                String description = o.get("description").getAsString();
                String epl = o.get("epl").getAsString();
                String type = o.has("type") ? o.get("type").getAsString() : "atomic";

                ConfidenceRule confRule = null;
                if (type.equals("complex") && o.has("confidence")) {
                    var conf = o.getAsJsonObject("confidence");
                    confRule = new ConfidenceRule(conf.get("aggregation").getAsString());
                }
                defs.add(new PatternDef(name, description, epl, type, confRule));
            }
        }

        this.patterns = defs;
        LOG.info("[EsperPatternManager] Loaded " + defs.size() + " patterns");
    }

    // ---------------------------------------------------------------------
    // Deploy compiled EPLs to Esper runtime
    // ---------------------------------------------------------------------
    @Override
    public void deployPatterns() throws Exception {
        EPRuntime rt = engine.getRuntime();
        Configuration cfg = engine.getConfiguration();
        CompilerArguments args = new CompilerArguments(cfg);

        for (PatternDef def : patterns) {
            EPCompiled compiled = compiler.compile(def.epl, args);
            EPDeployment dep = rt.getDeploymentService().deploy(compiled);
            attachListener(def, dep, rt);
        }

        LOG.info("[EsperPatternManager] Deployed " + patterns.size() + " patterns.");
    }

    // ---------------------------------------------------------------------
    // Listener for pattern detections
    // ---------------------------------------------------------------------
    private void attachListener(PatternDef def, EPDeployment dep, EPRuntime rt) {
        for (EPStatement stmt : dep.getStatements()) {
            stmt.addListener((newData, oldData, s, r) -> {
                if (newData == null || newData.length == 0) return;

                List<Event> baseEvents = new ArrayList<>();
                List<Pattern> subPatterns = new ArrayList<>();

                for (String prop : newData[0].getEventType().getPropertyNames()) {
                    Object v = newData[0].get(prop);
                    if (v instanceof Event e) baseEvents.add(e);
                    else if (v instanceof Pattern p) subPatterns.add(p);
                }

                Pattern record;
                if (def.type.equals("atomic")) {
                    double conf = baseEvents.stream()
                            .map(Event::getConfidence)
                            .filter(Objects::nonNull)
                            .mapToDouble(Double::doubleValue)
                            .average()
                            .orElse(1.0);
                    record = new AtomicPattern(def.name, baseEvents, conf);
                } else {
                    double conf = aggregate(
                            subPatterns.stream().map(Pattern::getConfidence).toList(),
                            def.confidence);
                    record = new ComplexPattern(def.name, subPatterns);
                    record.setConfidence(conf);
                }

                // Log and emit
                patternLogger.log(record);
                rt.getEventService().sendEventBean(record, "PatternRecordStream");

                // if (logMatches) {
                //     LOG.info(String.format(
                //         "[CEP] Fired %s %s | conf=%.3f | sources=%s",
                //         def.type,
                //         def.name,
                //         record.getConfidence(),
                //         record.getSourceIdsAsString()
                //     ));
                // }
            });
        }
    }


    // ---------------------------------------------------------------------
    // Confidence aggregation rule
    // ---------------------------------------------------------------------
    private double aggregate(List<Double> vals, ConfidenceRule rule) {
        if (vals == null || vals.isEmpty() || rule == null) return 0.0;

        return switch (rule.method) {
            case "min" -> vals.stream().mapToDouble(Double::doubleValue).min().orElse(0.0);
            case "max" -> vals.stream().mapToDouble(Double::doubleValue).max().orElse(0.0);
            case "avg" -> vals.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
            case "most_recent" -> {
                // Find the most recent imputed (confidence < 1.0) value
                for (int i = vals.size() - 1; i >= 0; i--) {
                    double v = vals.get(i);
                    if (v < 1.0) yield v;
                }
                yield vals.get(vals.size() - 1);
            }
            default -> vals.get(vals.size() - 1);
        };
    }
}
