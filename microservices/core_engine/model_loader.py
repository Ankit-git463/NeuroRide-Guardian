import joblib
import numpy as np
import pandas as pd
import warnings

class MaintenancePredictor:
    def __init__(self,
                 model_path='D:/EYSOLUTION/maintenance-predictor/backend/maintenance_rf_model.pkl',
                 fallback_feature_names=None):
        """Load the trained model and determine expected feature names.

        If the fitted estimator contains `feature_names_in_` (common when fit on a DataFrame),
        we use that as the ground truth. Otherwise we use the provided fallback_feature_names.
        """
        try:
            self.model = joblib.load(model_path)
            print(f"Model loaded. Type: {type(self.model)}")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

        # Try to infer expected feature names from the loaded model (best option)
        self.expected_features = None
        try:
            # If pipeline: try pipeline.get_feature_names_out()
            if hasattr(self.model, "get_feature_names_out"):
                # This returns the final output feature names for pipelines that support it
                self.expected_features = list(self.model.get_feature_names_out())
                print("Using feature names from model.get_feature_names_out()")
            # If pipeline with named_steps, final estimator might have feature_names_in_
            elif hasattr(self.model, "named_steps"):
                # Try final estimator in pipeline
                final_estimator = list(self.model.named_steps.values())[-1]
                if hasattr(final_estimator, "feature_names_in_"):
                    self.expected_features = list(final_estimator.feature_names_in_)
                    print("Using feature names from pipeline final_estimator.feature_names_in_")
            # Direct estimator with feature_names_in_
            elif hasattr(self.model, "feature_names_in_"):
                self.expected_features = list(self.model.feature_names_in_)
                print("Using feature names from model.feature_names_in_")
        except Exception as ex:
            # If any introspection fails, we'll fallback below
            warnings.warn(f"Could not extract feature names automatically: {ex}")

        # If we couldn't infer, fall back to either user-supplied or the older list you had
        if self.expected_features is None:
            if fallback_feature_names is not None:
                self.expected_features = list(fallback_feature_names)
                print("Using provided fallback_feature_names")
            else:
                # Original feature list as fallback (kept for backward compatibility)
                self.expected_features = [
                    'Year_of_Manufacture', 'Vehicle_Type', 'Usage_Hours',
                    'Load_Capacity', 'Actual_Load', 'Maintenance_Cost',
                    'Tire_Pressure', 'Fuel_Consumption', 'Battery_Status',
                    'Vibration_Levels', 'Oil_Quality', 'Brake_Condition',
                    'Impact_on_Efficiency', 'Delivery_Times', 'Maintenance_Year',
                    'Maintenance_Month', 'Maintenance_Day', 'Maintenance_Weekday',
                    'Maintenance_Type_Engine Overhaul', 'Maintenance_Type_Oil Change',
                    'Maintenance_Type_Tire Rotation', 'Weather_Conditions_Clear',
                    'Weather_Conditions_Rainy', 'Weather_Conditions_Snowy',
                    'Weather_Conditions_Windy', 'Road_Conditions_Highway',
                    'Road_Conditions_Rural', 'Road_Conditions_Urban'
                ]
                print("Using built-in fallback feature list")

        # Normalize expected features to strings
        self.expected_features = [str(f) for f in self.expected_features]
        print(f"Number of expected features: {len(self.expected_features)}")

    def _zero_dataframe_for_expected(self):
        """Create a one-row DataFrame with all expected features set to 0."""
        return pd.DataFrame([{col: 0 for col in self.expected_features}])

    def prepare_input(self, input_data):
        """Prepare input data for prediction.

        - Accepts input_data as dict (frontend keys).
        - Fills missing expected features with 0.
        - Drops unexpected extras.
        - Reorders columns to exactly match expected_features order (crucial).
        """
        try:
            # Start from zeros for all expected features (ensures no missing columns)
            df = self._zero_dataframe_for_expected()

            # Mapping from frontend keys to model feature names (only for raw fields)
            field_mapping = {
                'year_of_manufacture': 'Year_of_Manufacture',
                'vehicle_type': 'Vehicle_Type',
                'usage_hours': 'Usage_Hours',
                'load_capacity': 'Load_Capacity',
                'actual_load': 'Actual_Load',
                'maintenance_cost': 'Maintenance_Cost',
                'tire_pressure': 'Tire_Pressure',
                'fuel_consumption': 'Fuel_Consumption',
                'battery_status': 'Battery_Status',
                'vibration_levels': 'Vibration_Levels',
                'oil_quality': 'Oil_Quality',
                'brake_condition': 'Brake_Condition',
                'impact_on_efficiency': 'Impact_on_Efficiency',
                'delivery_times': 'Delivery_Times',
                'maintenance_year': 'Maintenance_Year',
                'maintenance_month': 'Maintenance_Month',
                'maintenance_day': 'Maintenance_Day',
                'maintenance_weekday': 'Maintenance_Weekday'
            }

            # Helper to set a value if the target column exists in expected features
            def set_if_exists(df_row, col_name, value):
                if col_name in df_row.index:
                    df_row[col_name] = value
                else:
                    # note: keep silent — feature will remain as zero
                    warnings.warn(f"Feature '{col_name}' not in expected_features; skipping assignment.")

            # Work on the single-row Series for easier assignment
            row = df.iloc[0]

            # Assign mapped fields
            for frontend_key, model_key in field_mapping.items():
                if frontend_key in input_data:
                    try:
                        # cast numeric-like inputs to float; keep strings as-is
                        val = input_data[frontend_key]
                        if isinstance(val, (int, float, str)):
                            # attempt numeric cast for numeric fields; keep string for vehicle_type
                            if model_key not in ('Vehicle_Type',):
                                val = float(val)
                        row[model_key] = val
                    except Exception:
                        # keep default 0 if casting fails
                        warnings.warn(f"Could not cast value for '{frontend_key}' -> '{model_key}'; leaving default 0")

            # Handle vehicle_type specially: if model expects a numeric Vehicle_Type, use as-is.
            # If model uses one-hot vehicle_type_* columns, map accordingly (simple heuristics)
            if 'vehicle_type' in input_data:
                v = str(input_data['vehicle_type']).strip()
                # Try direct column 'Vehicle_Type'
                if 'Vehicle_Type' in row.index:
                    # try to cast to numeric if possible, else keep string (the pipeline should handle it)
                    try:
                        row['Vehicle_Type'] = float(v)
                    except Exception:
                        row['Vehicle_Type'] = v
                else:
                    # Look for one-hot style columns that contain 'vehicle' or the vehicle value
                    for col in row.index:
                        if col.lower().startswith('vehicle_type_'):
                            # check if the category name appears in the column (case-insensitive)
                            if v.lower().replace(" ", "_") in col.lower():
                                row[col] = 1

            # Set some sensible defaults for one-hot features if present
            # (you used these defaults previously)
            defaults = {
                'Maintenance_Type_Oil Change': 1,
                'Weather_Conditions_Clear': 1,
                'Road_Conditions_Highway': 1
            }
            for k, v in defaults.items():
                if k in row.index:
                    row[k] = v

            # Re-create df from the modified row (ensures types preserved)
            df = pd.DataFrame([row])

            # Drop unexpected extras (shouldn't be any because we started from expected list)
            extras = [c for c in df.columns if c not in self.expected_features]
            if extras:
                df = df.drop(columns=extras)

            # Reorder to exactly expected order (this is what sklearn's check enforces)
            df = df[self.expected_features]

            print(f"Prepared input shape: {df.shape}")
            # rigorous equality check (order+names)
            print(f"Feature names match: {list(df.columns) == self.expected_features}")

            return df

        except Exception as e:
            print(f"Error in prepare_input: {e}")
            raise

    def predict(self, input_data):
        """Make prediction. Returns a dict with maintenance_required, probability (if available), confidence."""
        try:
            X = self.prepare_input(input_data)

            # final model might be a pipeline — pipeline.predict will handle preprocessing
            prediction = self.model.predict(X)[0]

            probability_pos = None
            confidence_pct = None
            try:
                proba = self.model.predict_proba(X)[0]
                # If binary classification, class 1 probability is proba[1]; otherwise try highest class
                if len(proba) >= 2:
                    probability_pos = float(proba[1])
                else:
                    # multiclass fallback: probability of predicted class
                    probability_pos = float(proba[int(prediction)])
                confidence_pct = float(max(proba) * 100)
            except AttributeError:
                # model doesn't support predict_proba
                warnings.warn("Model has no predict_proba; returning prediction without probability.")
            except Exception as e:
                warnings.warn(f"predict_proba failed: {e}")

            result = {
                'maintenance_required': int(prediction),
                'probability': probability_pos if probability_pos is not None else None,
                'confidence': confidence_pct if confidence_pct is not None else None
            }

            print(f"Prediction result: {result}")
            return result

        except Exception as e:
            print(f"Error in predict: {e}")
            raise
