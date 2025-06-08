dev:
	maturin develop --release

test: dev
	python -m pytest tests/ -v

test-perf: dev
	python -m pytest tests/test_performance.py -s -v

test-api: dev
	python -m pytest tests/test_api.py -s -v

clean:
	cargo clean
	rm -rf target/