use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyTuple, PySet};
use std::collections::HashMap;
use serde_json::Value;

#[pyclass]
struct DeepDiff {
    #[pyo3(get)]
    values_changed: HashMap<String, PyObject>,
    #[pyo3(get)]
    type_changes: HashMap<String, PyObject>,
    #[pyo3(get)]
    dictionary_item_added: HashMap<String, PyObject>,
    #[pyo3(get)]
    dictionary_item_removed: HashMap<String, PyObject>,
    #[pyo3(get)]
    iterable_item_added: HashMap<String, PyObject>,
    #[pyo3(get)]
    iterable_item_removed: HashMap<String, PyObject>,
}

#[pymethods]
impl DeepDiff {
    #[new]
    fn new() -> Self {
        DeepDiff {
            values_changed: HashMap::new(),
            type_changes: HashMap::new(),
            dictionary_item_added: HashMap::new(),
            dictionary_item_removed: HashMap::new(),
            iterable_item_added: HashMap::new(),
            iterable_item_removed: HashMap::new(),
        }
    }

    fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let result = PyDict::new(py);
        
        if !self.values_changed.is_empty() {
            let values_dict = PyDict::new(py);
            for (k, v) in &self.values_changed {
                values_dict.set_item(k, v.clone_ref(py))?;
            }
            result.set_item("values_changed", values_dict)?;
        }
        
        if !self.type_changes.is_empty() {
            let types_dict = PyDict::new(py);
            for (k, v) in &self.type_changes {
                types_dict.set_item(k, v.clone_ref(py))?;
            }
            result.set_item("type_changes", types_dict)?;
        }
        
        if !self.dictionary_item_added.is_empty() {
            let added_dict = PyDict::new(py);
            for (k, v) in &self.dictionary_item_added {
                added_dict.set_item(k, v.clone_ref(py))?;
            }
            result.set_item("dictionary_item_added", added_dict)?;
        }
        
        if !self.dictionary_item_removed.is_empty() {
            let removed_dict = PyDict::new(py);
            for (k, v) in &self.dictionary_item_removed {
                removed_dict.set_item(k, v.clone_ref(py))?;
            }
            result.set_item("dictionary_item_removed", removed_dict)?;
        }
        
        if !self.iterable_item_added.is_empty() {
            let added_dict = PyDict::new(py);
            for (k, v) in &self.iterable_item_added {
                added_dict.set_item(k, v.clone_ref(py))?;
            }
            result.set_item("iterable_item_added", added_dict)?;
        }
        
        if !self.iterable_item_removed.is_empty() {
            let removed_dict = PyDict::new(py);
            for (k, v) in &self.iterable_item_removed {
                removed_dict.set_item(k, v.clone_ref(py))?;
            }
            result.set_item("iterable_item_removed", removed_dict)?;
        }
        
        Ok(result.into())
    }
}

#[pyfunction]
fn compare(py: Python, t1: PyObject, t2: PyObject) -> PyResult<PyObject> {
    let mut diff = DeepDiff::new();
    compare_objects(py, t1, t2, "root".to_string(), &mut diff)?;
    Ok(diff.to_dict(py)?)
}

fn compare_objects(py: Python, t1: PyObject, t2: PyObject, path: String, diff: &mut DeepDiff) -> PyResult<()> {
    let t1_type = t1.as_ref(py).get_type();
    let t2_type = t2.as_ref(py).get_type();
    
    if !t1_type.is(t2_type) {
        let change = PyDict::new(py);
        change.set_item("old_type", t1_type.name()?)?;
        change.set_item("new_type", t2_type.name()?)?;
        change.set_item("old_value", t1.clone_ref(py))?;
        change.set_item("new_value", t2.clone_ref(py))?;
        diff.type_changes.insert(path, change.into());
        return Ok(());
    }
    
    if let (Ok(d1), Ok(d2)) = (t1.extract::<&PyDict>(py), t2.extract::<&PyDict>(py)) {
        compare_dicts(py, d1, d2, path, diff)?;
    }
    else if let (Ok(l1), Ok(l2)) = (t1.extract::<&PyList>(py), t2.extract::<&PyList>(py)) {
        compare_iterables(py, l1.iter().collect(), l2.iter().collect(), path, diff)?;
    }
    else if let (Ok(t1_tuple), Ok(t2_tuple)) = (t1.extract::<&PyTuple>(py), t2.extract::<&PyTuple>(py)) {
        compare_iterables(py, t1_tuple.iter().collect(), t2_tuple.iter().collect(), path, diff)?;
    }
    else if let (Ok(s1), Ok(s2)) = (t1.extract::<&PySet>(py), t2.extract::<&PySet>(py)) {
        let s1_len = s1.len();
        let s2_len = s2.len();
        
        if s1_len != s2_len {
            let change = PyDict::new(py);
            change.set_item("old_value", t1.clone_ref(py))?;
            change.set_item("new_value", t2.clone_ref(py))?;
            diff.values_changed.insert(path, change.into());
        } else {
            let py_s1: PyObject = s1.into();
            let py_s2: PyObject = s2.into();
            let is_equal = py.import("operator")?.getattr("eq")?.call1((py_s1, py_s2))?;
            
            if !is_equal.extract::<bool>()? {
                let change = PyDict::new(py);
                change.set_item("old_value", t1.clone_ref(py))?;
                change.set_item("new_value", t2.clone_ref(py))?;
                diff.values_changed.insert(path, change.into());
            }
        }
    }
    else {
        let is_equal = py.import("operator")?.getattr("eq")?.call1((t1.clone_ref(py), t2.clone_ref(py)))?;
        
        if !is_equal.extract::<bool>()? {
            let change = PyDict::new(py);
            change.set_item("old_value", t1.clone_ref(py))?;
            change.set_item("new_value", t2.clone_ref(py))?;
            diff.values_changed.insert(path, change.into());
        }
    }
    
    Ok(())
}

fn compare_dicts(py: Python, d1: &PyDict, d2: &PyDict, path: String, diff: &mut DeepDiff) -> PyResult<()> {
    for (k, v1) in d1.iter() {
        let key_str = k.to_string();
        let new_path = format!("{}.{}", path, key_str);
        
        if let Some(v2) = d2.get_item(k) {
            compare_objects(py, v1.into(), v2.into(), new_path, diff)?;
        } else {
            diff.dictionary_item_removed.insert(new_path, v1.into());
        }
    }
    
    for (k, v2) in d2.iter() {
        if d1.get_item(k).is_none() {
            let key_str = k.to_string();
            let new_path = format!("{}.{}", path, key_str);
            diff.dictionary_item_added.insert(new_path, v2.into());
        }
    }
    
    Ok(())
}

fn compare_iterables(py: Python, l1: Vec<&PyAny>, l2: Vec<&PyAny>, path: String, diff: &mut DeepDiff) -> PyResult<()> {
    for i in 0..std::cmp::min(l1.len(), l2.len()) {
        let new_path = format!("{}[{}]", path, i);
        compare_objects(py, l1[i].into(), l2[i].into(), new_path, diff)?;
    }
    
    for i in l2.len()..l1.len() {
        let new_path = format!("{}[{}]", path, i);
        diff.iterable_item_removed.insert(new_path, l1[i].into());
    }
    
    for i in l1.len()..l2.len() {
        let new_path = format!("{}[{}]", path, i);
        diff.iterable_item_added.insert(new_path, l2[i].into());
    }
    
    Ok(())
}

#[derive(Debug, Clone, PartialEq)]
pub enum PathComponent {
    Key(String),
    Index(usize),
}

fn format_path(path: &[PathComponent]) -> String {
    let mut result = String::from("root");
    
    for component in path {
        match component {
            PathComponent::Key(key) => {
                result.push_str(&format!("['{}']", key));
            }
            PathComponent::Index(idx) => {
                result.push_str(&format!("[{}]", idx));
            }
        }
    }
    
    result
}

#[derive(Debug, Clone)]
pub struct Diff {
    pub added: HashMap<String, Value>,
    pub removed: HashMap<String, Value>,
    pub changed: HashMap<String, Value>,
    pub iterable_item_added: HashMap<String, Value>,
    pub iterable_item_removed: HashMap<String, Value>,
}

fn compare_values(_diff: &mut Diff, _old_json: &Value, _new_json: &Value, _path: Vec<PathComponent>) {
    // Реализация сравнения значений JSON
    // Это заглушка, которую нужно заменить реальной реализацией
}

pub fn generate_diff(old_json: &Value, new_json: &Value) -> Diff {
    let mut diff = Diff {
        added: HashMap::new(),
        removed: HashMap::new(),
        changed: HashMap::new(),
        iterable_item_added: HashMap::new(),
        iterable_item_removed: HashMap::new(),
    };

    compare_values(&mut diff, old_json, new_json, vec![]);
    
    let reformat_hashmap = |map: HashMap<String, Value>| -> HashMap<String, Value> {
        let mut new_map = HashMap::new();
        for (path_str, value) in map {
            let path_components: Vec<PathComponent> = parse_path(&path_str);
            let new_path_str = format_path(&path_components);
            new_map.insert(new_path_str, value);
        }
        new_map
    };
    
    Diff {
        added: reformat_hashmap(diff.added),
        removed: reformat_hashmap(diff.removed),
        changed: reformat_hashmap(diff.changed),
        iterable_item_added: reformat_hashmap(diff.iterable_item_added),
        iterable_item_removed: reformat_hashmap(diff.iterable_item_removed),
    }
}

fn parse_path(_path_str: &str) -> Vec<PathComponent> {
    // Реализация парсинга строки пути в компоненты
    // Это зависит от текущего формата путей в вашей библиотеке
    // ...
    vec![] // Заглушка
}

#[allow(dead_code)]
fn path_to_string(path: &[PathComponent]) -> String {
    let mut result = String::from("root");
    
    for component in path {
        match component {
            PathComponent::Key(key) => {
                result.push_str(&format!("['{}']", key));
            }
            PathComponent::Index(idx) => {
                result.push_str(&format!("[{}]", idx));
            }
        }
    }
    
    result
}

#[pymodule]
fn rustdeepdiff(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<DeepDiff>()?;
    m.add_function(wrap_pyfunction!(compare, m)?)?;
    Ok(())
} 