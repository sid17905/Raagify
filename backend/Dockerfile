FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -B -ntp dependency:go-offline
COPY src src
RUN mvn -B -ntp -DskipTests package
FROM eclipse-temurin:21-jre
WORKDIR /app
RUN mkdir -p /data/audio /data/covers && useradd -r -u 10001 raagify && chown -R raagify /app /data
COPY --from=build /app/target/raagify-backend-1.0.0.jar app.jar
USER raagify
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
