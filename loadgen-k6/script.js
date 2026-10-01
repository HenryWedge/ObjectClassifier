import encoding from "k6/encoding";
import { randomSeed } from "k6";
import { SharedArray } from "k6/data";
import { Writer } from "k6/x/kafka";

const bootstrapServer = __ENV.BOOTSTRAP_SERVER || "kafka-kafka-bootstrap.object-classifier-two-zone-cloud.svc:9092";
const topic = __ENV.TOPIC || "dog-input";
const seed = Number(__ENV.SEED || "42");

const sendIntervalSeconds = Number(__ENV.SEND_INTERVAL_SECONDS || "1.0");
const envArrivalRate = __ENV.ARRIVAL_RATE ? Number(__ENV.ARRIVAL_RATE) : NaN;
const arrivalRate = Number.isFinite(envArrivalRate)
  ? envArrivalRate
  : sendIntervalSeconds > 0
    ? 1 / sendIntervalSeconds
    : 1;

if (!Number.isFinite(arrivalRate) || arrivalRate <= 0) {
  throw new Error("ARRIVAL_RATE must be a number > 0 (or SEND_INTERVAL_SECONDS must be > 0)");
}

const duration = __ENV.DURATION || "10m";
const preAllocatedVUs = Number(__ENV.PRE_ALLOCATED_VUS || "10");
const maxVUs = Number(__ENV.MAX_VUS || "200");
const imageFilesCsvPath = __ENV.IMAGE_FILES_CSV_PATH || "/app/image-files.csv";

if (!Number.isFinite(preAllocatedVUs) || preAllocatedVUs <= 0) {
  throw new Error("PRE_ALLOCATED_VUS must be a number > 0");
}
if (!Number.isFinite(maxVUs) || maxVUs <= 0) {
  throw new Error("MAX_VUS must be a number > 0");
}

export const options = {
  scenarios: {
    kafka_producer: {
      executor: "constant-arrival-rate",
      rate: arrivalRate,
      timeUnit: "1s",
      duration,
      preAllocatedVUs,
      maxVUs,
    },
  },
};

const imageFilesEnv = __ENV.IMAGE_FILES || open(imageFilesCsvPath);
const imagePaths = imageFilesEnv
  .split(",")
  .map((path) => path.trim())
  .filter((path) => path.length > 0);

if (imagePaths.length === 0) {
  throw new Error(
    "No images configured. Please set IMAGE_FILES as a comma-separated list, e.g. /data/images/n02085620-Chihuahua/dog.jpg,/data/images/n02085936-Maltese/m1.jpg",
  );
}

function parseLabelFromParent(imagePath) {
  const segments = imagePath.replaceAll("\\", "/").split("/").filter(Boolean);
  const parent = segments.length > 1 ? segments[segments.length - 2] : "";
  const separatorIndex = parent.indexOf("-");
  if (separatorIndex >= 0 && separatorIndex < parent.length - 1) {
    return parent.slice(separatorIndex + 1);
  }
  return parent;
}

const images = new SharedArray("images", () => {
  return imagePaths.map((imagePath) => {
    const raw = open(imagePath, "b");
    return {
      path: imagePath,
      label: parseLabelFromParent(imagePath),
      data: encoding.b64encode(raw),
    };
  });
});

const writer = new Writer({
  brokers: [bootstrapServer],
  topic,
});

randomSeed(seed);

export function setup() {
  console.log(
    `Starting k6 Kafka producer with ${images.length} images, topic=${topic}, bootstrap=${bootstrapServer}, seed=${seed}, arrivalRate=${arrivalRate}/s, duration=${duration}`,
  );
}

export default function () {
  const selected = images[Math.floor(Math.random() * images.length)];
  const payload = {
    data: selected.data,
    timestamp: Date.now() / 1000,
    label: selected.label,
  };

  writer.produce({
    messages: [{ value: encoding.b64encode(JSON.stringify(payload)) }],
  });
}

export function teardown() {
  writer.close();
}
